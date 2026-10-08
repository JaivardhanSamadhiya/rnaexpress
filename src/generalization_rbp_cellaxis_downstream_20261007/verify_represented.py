"""Independent SAME-checkpoint both-state scores/choices and old control replay."""
from .common import *
from .evaluate import selected_model
from .numeric import canonical,decisions,equal_decisions,task_summary
from .verify import prediction_roster


def run(root_start=False):
    assert root_start;evaluation_check();np,pd,*_=runtime();frame=load()
    from src.generalization_knowncell_20261007.splits import masks
    assert not (OUT/'represented_verification_receipt.json').exists()
    counts=0;maximum=0.;saved_max=0.;files={}
    for track in s.TRACKS:
        folder=OUT/'represented'/track;x=features(track)
        complete=readj(folder/'complete.json');assert complete['status']=='PASS' and complete['fits']==0 and complete['evaluation_sha256']==sha256(EVALUATION)
        p=pd.read_csv(folder/'predictions.csv.gz',float_precision='round_trip')
        d=pd.read_csv(folder/'decisions.csv',float_precision='round_trip');prediction_roster(p,d,frame,track,s.KNOWN_TASKS)
        roster=readj(folder/'roster.json');assert len(roster)==6
        assert {(r['task'],r['fold']) for r in roster}=={(t,f) for t in s.KNOWN_TASKS for f in s.FOLDS}
        source_folder=OLD_OUT/track if track in s.REUSED_CONTROLS else OUT/'crossed'/track
        crossed_p=pd.read_csv(source_folder/'predictions.csv.gz',float_precision='round_trip')
        crossed_d=pd.read_csv(source_folder/'decisions.csv',float_precision='round_trip');prediction_roster(crossed_p,crossed_d,frame,track,s.TASKS)
        for task,(_,source_task) in s.KNOWN_TASKS.items():
            for fold in s.FOLDS:
                tr,te,opposite=masks(frame,task,fold)
                model,config,original_train,original_target,path=selected_model(track,source_task,fold,frame,x)
                np.testing.assert_array_equal(tr,original_train);np.testing.assert_array_equal(opposite,original_target)
                info=next(r for r in roster if (r['task'],r['fold'])==(task,fold))
                assert info['checkpoint']==path.relative_to(ROOT).as_posix() and info['checkpoint_sha256']==sha256(path)
                assert info['configuration']==config and info['source_task']==source_task
                assert info['training_ids_sha256']==rowhash(frame.loc[tr])
                for mask,state,pred,dec in ((te,task,p,d),(opposite,source_task,crossed_p,crossed_d)):
                    target=frame.loc[mask].reset_index(drop=True);score,error=canonical(model,x[mask]);maximum=max(maximum,error)
                    observed=pred[pred.task.eq(state)&pred.gene_fold.eq(fold)].set_index('intervention_id').loc[target.intervention_id]
                    assert set(observed.configuration)=={config['id']}
                    error_saved=float(np.max(abs(score-observed.score.to_numpy(float))));assert error_saved<1e-9
                    saved_max=max(saved_max,error_saved);equal_decisions(decisions(target,score),dec[dec.task.eq(state)&dec.gene_fold.eq(fold)])
                    if mask is te:
                        assert info['target_ids_sha256']==rowhash(target) and info['target_metadata_sha256']==metadata_hash(target)
                        assert info['target_labels_sha256']==values_hash(target.measured_delta)
                if track in s.REUSED_CONTROLS:
                    old_pred=pd.read_csv(OLD_KNOWN/track/'predictions.csv.gz',float_precision='round_trip')
                    old_d=pd.read_csv(OLD_KNOWN/track/'decisions.csv',float_precision='round_trip')
                    target=frame.loc[te].reset_index(drop=True);score,_=canonical(model,x[te])
                    old_scores=old_pred[old_pred.task.eq(task)&old_pred.gene_fold.eq(fold)].set_index('intervention_id').loc[target.intervention_id]
                    assert set(old_scores.configuration)=={config['id']}
                    np.testing.assert_allclose(score,old_scores.score,atol=1e-9,rtol=0)
                    equal_decisions(decisions(target,score),old_d[old_d.task.eq(task)&old_d.gene_fold.eq(fold)])
                counts+=1
        actual=task_summary(d).sort_values('task').reset_index(drop=True)
        stored=pd.read_csv(folder/'comparison.csv',float_precision='round_trip').sort_values('task').reset_index(drop=True)
        pd.testing.assert_frame_equal(actual,stored,check_exact=False,atol=1e-12,rtol=0)
        for path in folder.rglob('*'):
            if path.is_file():files[path.relative_to(ROOT).as_posix()]=sha256(path)
        print('Represented both-state independent replay',track,'PASS',flush=True);del x
    assert counts==36;evaluation_check()
    jsave(OUT/'represented_verification_receipt.json',{'status':'PASS','same_checkpoint_both_states_verified':True,
        'checkpoints':36,'state_predictions_replayed':72,'old_simple_base_known_controls_replayed':12,
        'evaluation_sha256':sha256(EVALUATION),'maximum_independent_score_error':maximum,
        'maximum_saved_score_error':saved_max,'files':files,'new_fits':0,'full_original_menus':True,
        'original_ID_ties_and_truths':True,'independent_confirmation':False})


if __name__=='__main__':
    import sys
    run('--root-start' in sys.argv[1:])
