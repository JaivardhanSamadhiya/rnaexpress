"""Represented-cell targets, identical source checkpoints, ZERO new fits."""
from .common import *
from .numeric import task_summary
from .checkpoints import identity,checked,verify_numerics
from src.generalization_rbp_cellaxis_20261007.contracts import source_choice


def selected_model(track,source_task,fold,frame,x):
    if track in s.REUSED_CONTROLS:
        from .controls import selected_model as old
        return old(track,source_task,fold,frame,x)
    np,pd,*_=runtime()
    from src.generalization_crosscell_20261007.splits import outer_masks
    folder=OUT/'crossed'/track;roster=readj(folder/'folds.json')
    assert len(roster)==6 and {(r['task'],r['fold']) for r in roster}=={(t,f) for t in s.TASKS for f in s.FOLDS}
    info=next(r for r in roster if (r['task'],r['fold'])==(source_task,fold))
    table=pd.read_csv(folder/'source_selection.csv',float_precision='round_trip');values=[]
    for config in s.CONFIGS:
        row=table[table.task.eq(source_task)&table.outer_fold.eq(fold)&table.configuration.eq(config['id'])]
        assert len(row)==1;value=float(row.iloc[0].combined_source_oof_macro_regret)
        assert abs(value-info['all_source_oof_scores'][config['id']])<1e-12;values.append(value)
    config=source_choice(values);assert config==info['selected_configuration']
    train,test=outer_masks(frame,source_task,fold);source=frame.loc[train].reset_index(drop=True)
    path=folder/'fits'/(source_task+'__fold'+str(fold)+'__outer_'+config['id']+'.json')
    model=checked(path,identity(track,source,x[train],config),config)
    verify_numerics(model,source,x[train],config)
    assert rowhash(source)==info['training_ids_sha256'] and rowhash(frame.loc[test])==info['test_ids_sha256']
    return model,config,train,test,path


def run(root_start=False):
    assert root_start;evaluation_check();resource_check();np,pd,old,_,predict=runtime()
    from src.generalization_knowncell_20261007.splits import masks
    assert not (OUT/'represented_evaluation_complete.json').exists();frame=load()
    for track in s.TRACKS:
        folder=OUT/'represented'/track;assert not (folder/'complete.json').exists()
        x=features(track);predictions=[];pieces=[];roster=[]
        for task,(_,source_task) in s.KNOWN_TASKS.items():
            for fold in s.FOLDS:
                train,test,opposite=masks(frame,task,fold)
                model,config,original_train,original_target,path=selected_model(track,source_task,fold,frame,x)
                np.testing.assert_array_equal(train,original_train);np.testing.assert_array_equal(opposite,original_target)
                target=frame.loc[test].reset_index(drop=True);score=predict(model,x[test])
                d=old.decisions(target,score,track);d['task']=task;d['gene_fold']=fold;pieces.append(d)
                predictions.extend({'track':track,'task':task,'gene_fold':fold,'intervention_id':row.intervention_id,
                    'score':float(score[i]),'configuration':config['id']} for i,row in enumerate(target.itertuples()))
                roster.append({'task':task,'fold':fold,'source_task':source_task,'configuration':config,
                    'checkpoint':path.relative_to(ROOT).as_posix(),'checkpoint_sha256':sha256(path),
                    'training_ids_sha256':rowhash(frame.loc[train]),'target_ids_sha256':rowhash(target),
                    'target_metadata_sha256':metadata_hash(target),'target_labels_sha256':values_hash(target.measured_delta)})
        assert len(predictions)==s.ROWS and len({r['intervention_id'] for r in predictions})==s.ROWS
        d=pd.concat(pieces,ignore_index=True)
        csvsave(folder/'predictions.csv.gz',pd.DataFrame(predictions),True);csvsave(folder/'decisions.csv',d)
        csvsave(folder/'comparison.csv',task_summary(d));jsave(folder/'roster.json',roster)
        jsave(folder/'complete.json',{'status':'PASS','track':track,'rows':s.ROWS,'fits':0,'evaluation_sha256':sha256(EVALUATION)})
        print('Represented-cell',track,'six unchanged source predictors complete',flush=True)
        del x
    evaluation_check()
    jsave(OUT/'represented_evaluation_complete.json',{'status':'PASS','tracks':s.TRACKS,'outer_models_reused':36,
        'new_fits':0,'evaluation_sha256':sha256(EVALUATION),'independent_confirmation':False})


if __name__=='__main__':
    import sys
    run('--root-start' in sys.argv[1:])
