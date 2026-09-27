from .common import *
import subprocess,sys

def run():
    source,effects,choices,fits,roster=load()
    pred=pd.read_csv(OLDART/'srle_heldout_predictions.csv',dtype={'group':str},float_precision='round_trip')
    strict=pred[pred.scheme.eq('purged_composition_holdout')]
    bundle={'schema':1,'scope':'Frozen held-out replay; no new RNA inference','parents':{},'scores':{},'folds':{},'cohort_risk':{}}
    for parent,g in roster.groupby('parent'):bundle['parents'][parent]={'candidates':sorted(g.candidate.tolist()),'group':g.group.iloc[0]}
    for model in ('2mer','kmer123'):
        g=strict[strict.model.eq(model)];bundle['scores'][model]=dict(zip(g.kmer,g.predicted_score))
        r=choices[choices.scheme.eq('purged_composition_holdout')&choices.model.eq(model)].groupby('group').wrong_both.mean().mean()
        bundle['cohort_risk'][model]={'wrong_both':r,'biological_contexts':1,'individual_risk_calibrated':False}
    for f in fits:
        if f['scheme']!='purged_composition_holdout':continue
        bundle['folds'][f['held_group']]={}
        for model in ('2mer','kmer123'):
            c=f['coefficients'][model];bundle['folds'][f['held_group']][model]=(np.array(c['coefficient'])/np.array(c['scale'])).tolist()
    jsave(ART/'prototype_bundle.json',bundle)
    jsave(ART/'prototype_manifest.json',{'bundle_sha256':sha256(ART/'prototype_bundle.json'),'source_prediction_sha256':sha256(OLDART/'srle_heldout_predictions.csv'),'source_coefficients_sha256':sha256(OLD/'fitted_parameters.json'),'source_freeze_commit':'0023b01','outcome_policy':'No sequence-level experimental outcomes in runtime bundle. Only preexisting aggregate cohort risk.'})
    import predict_edit_candidates as interface
    runtime=interface.load_bundle();expected=choices[choices.scheme.eq('purged_composition_holdout')&choices.model.isin(['2mer','kmer123'])]
    checked=0
    for row in expected.itertuples():
        candidate_list=bundle['parents'][row.parent]['candidates']
        result=interface.predict(row.parent,candidate_list,'increase' if row.direction==1 else 'decrease',row.model,runtime)
        assert result['candidates'][0]['candidate']==row.selected
        assert abs(result['candidates'][0]['predicted_effect']-row.predicted_delta)<1e-15
        checked+=1
    examples=pd.read_csv(OUT/'representative_examples.csv',dtype={'group':str});demo=[]
    for row in examples.itertuples():
        direction='increase' if row.direction==1 else 'decrease';name=f'{direction}_{row.example_type}_{row.parent}'
        cf=ART/(name+'_candidates.txt');save(cf,('\n'.join(bundle['parents'][row.parent]['candidates'])+'\n').encode())
        command=[sys.executable,str(ROOT/'predict_edit_candidates.py'),'--parent',row.parent,'--candidates',str(cf),'--direction',direction]
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=True)
        obj=json.loads(result.stdout);assert obj['candidates'][0]['candidate']==row.selected
        jsave(ART/(name+'_prediction.json'),obj)
        demo.append({'name':name,'parent':row.parent,'direction':direction,'selected':row.selected,'candidate_file':cf.relative_to(ROOT).as_posix(),'prediction_file':(ART/(name+'_prediction.json')).relative_to(ROOT).as_posix(),'measured_published_delta':row.published_measured_delta,'rep1_delta':row.rep1_measured_delta,'rep2_delta':row.rep2_measured_delta,'wrong_both':row.wrong_both,'published_regret':row.published_regret,'selection_rule':'median average replicate regret within correct-both/wrong-both direction subgroup; lexical tie'})
    csvsave(OUT/'prototype_demo_outcomes.csv',pd.DataFrame(demo))
    jsave(OUT/'prototype_receipt.json',{'status':'PASS','frozen_decisions_replayed':checked,'parents':len(bundle['parents']),'models':2,'cli_demos':len(demo),'sequence_level_outcomes_in_runtime':False,'new_sequence_predictions_allowed':False})
    print(readj(OUT/'prototype_receipt.json'))

if __name__=='__main__':run()
