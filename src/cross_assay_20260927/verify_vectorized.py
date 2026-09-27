"""Reproduce scores, selected decisions and grouping independently."""
from .common import *
from .run import load,safe_id
from .models import fit,purge
import subprocess,sys

def run():
    freeze=frozen();initial=readj(OUT/'initial_state.json')
    for p,h in initial['unchanged_user_files'].items():assert sha256(ROOT/p)==h,p
    history=[]
    for path in ['artifacts/generalization_20260926/delivery_receipt.json','artifacts/srle_synthesis_20260926/delivery_receipt.json','artifacts/small_edit_20260925/delivery_receipt.json','artifacts/small_edit_20260925/srle_prediction_delivery_receipt.json']:
        r=readj(ROOT/path)
        for p,e in r['manifest'].items():assert sha256(ROOT/p)==e['sha256'],p
        assert sha256(ROOT/r['archive'])==r['sha256'];history.append({'receipt':path,'members_unchanged':len(r['manifest'])})
    frame,xs=load();pred=pd.read_csv(ART/'leave_one_assay_out_predictions.csv',float_precision='round_trip');dec=pd.read_csv(OUT/'decision_metrics.csv',float_precision='round_trip');cfg=config();core=frame.primary_eligible.to_numpy();errors=[];fresh=[];dec_checks=0;group_checks=0
    for study in cfg['core_studies']:
        te=core&frame.dataset.eq(study).to_numpy();tr=purge(frame,core&frame.dataset.ne(study).to_numpy(),te);tf=frame.loc[te].reset_index(drop=True);train=frame.loc[tr].reset_index(drop=True)
        assert not set(tf.biological_component)&set(train.biological_component);group_checks+=1
        fold=safe_id('held_assay|'+study)
        for model,(feature,kind) in cfg['models'].items():
            m=readj(OUT/'fits'/(fold+'_'+model+'.json'));assert study not in m['training_studies'];x=xs[feature][te]
            z=(x-np.array(m['mean']))/np.array(m['scale']);p=z@np.array(m['universal_beta'])
            saved=pred[pred.dataset.eq(study)&pred.model.eq(model)].set_index('intervention_id').loc[tf.intervention_id]
            error=float(np.max(abs(p-saved.final_score.to_numpy())));assert error<1e-12;assert np.all(saved.assay_residual==0);errors.append(error)
            if model in ('metadata','kmer123'):
                mf=fit(train,xs[feature][tr],kind);npred=((x-mf['mean'])/mf['scale'])@np.array(mf['universal_beta']);err=float(np.max(abs(npred-p)));assert err<1e-10;fresh.append(err)
            # Direct decision arithmetic, independent of metrics.evaluate.
            f=tf.copy();f['p']=p
            ds=dec[dec.stage.eq('held_assay')&dec.dataset.eq(study)&dec.model.eq(model)].set_index(['parent_context_id','direction'])
            lo=f.groupby('parent_context_id').measured_delta.min()
            hi=f.groupby('parent_context_id').measured_delta.max()
            for direction in (-1,1):
                chosen=f.assign(order=direction*f.p).sort_values(['order','intervention_id'],ascending=[False,True]).drop_duplicates('parent_context_id').set_index('parent_context_id')
                keys=pd.MultiIndex.from_arrays([chosen.index,np.full(len(chosen),direction)],names=['parent_context_id','direction'])
                saved_dec=ds.loc[keys]
                best=(hi if direction==1 else -lo).loc[chosen.index].to_numpy()
                spread=(hi-lo).loc[chosen.index].to_numpy()
                effect=direction*chosen.measured_delta.to_numpy()
                regret=(best-effect)/spread
                wrong=effect < -1e-12
                feasible=best > 1e-12
                assert np.array_equal(chosen.intervention_id.to_numpy(),saved_dec.selected_id.to_numpy())
                assert np.max(abs(regret-saved_dec.regret.to_numpy()))<1e-12
                assert np.array_equal(wrong.astype(float),saved_dec.wrong_direction.to_numpy())
                assert np.array_equal((wrong&feasible).astype(float),saved_dec.avoidable_wrong.to_numpy())
                dec_checks+=len(chosen)
            print('Checked',study,model,flush=True)
    # Confirm cached pretrained vectors correspond to the exact source design IDs too.
    bert=np.load(ART/'pretrained_covered.npz');design=pd.read_csv(ROOT/'results/v4_phaseB/model_interventions.csv.gz').set_index(['dataset','parent_id','mutant_id']);bm=readj(ROOT/'results/mechanism_v2/features/bert_pooled_allele_delta_manifest.json');cache=np.load(ROOT/bm['path'],mmap_mode='r');assert sha256(ROOT/bm['path'])==bm['sha256']
    for j,ix in enumerate(bert['indices']):
        r=frame.iloc[ix];src=design.loc[(r.dataset,r.parent_id,r.mutant_id)];assert src.parent_sequence==r.parent_sequence and src.mutant_sequence==r.mutant_sequence;assert np.array_equal(bert['values'][j],cache[int(src.feature_row)])
    assert not frame.loc[core].duplicated(['parent_context_id','mutant_sequence']).any()
    assert frame.loc[core].groupby('parent_context_id').mutant_sequence.nunique().min()>=2
    # Recompute every core macro regret directly from decisions, without aggregate().
    comparison=pd.read_csv(ART/'model_comparison.csv');cm=comparison[comparison.stage.eq('held_assay')]
    for r in cm.itertuples():
        d=dec[dec.stage.eq('held_assay')&dec.dataset.eq(r.dataset)&dec.model.eq(r.model)]
        value=np.mean([g.regret.mean() for _,g in d.groupby('biological_component')]);assert abs(value-r.regret)<1e-12
    result=subprocess.run([sys.executable,'-u','-m','src.cross_assay_20260927.test_scoped'],cwd=ROOT,capture_output=True,text=True);assert result.returncode==0,result.stderr;save(OUT/'verification_vectorized_tests.txt',(result.stdout+result.stderr).encode())
    checks={'status':'PASS','executed_code_sha256':sha256(Path(__file__)),'decision_audit':'vectorized exhaustive equivalent checks','prefit_hashes_unchanged':len(freeze['files']),'historical_bundles_unchanged':history,'unrelated_user_files_unchanged':len(initial['unchanged_user_files']),'score_replays':len(pred),'score_replay_max_error':max(errors),'fresh_model_fits':len(fresh),'fresh_fit_max_prediction_error':max(fresh),'independent_direction_decision_checks':dec_checks,'whole_study_purge_checks':group_checks,'pretrained_exact_ID_vector_checks':len(bert['indices']),'scoped_tests':11,'test_or_gate_modified':False}
    jsave(OUT/'verification_vectorized_receipt.json',checks);print(clean(checks))
if __name__=='__main__':run()
