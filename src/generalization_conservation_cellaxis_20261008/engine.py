"""Four fixed new nested pairwise tracks; original combined-source selector."""
from .common import *
from .checkpoints import fit
from .numeric import task_summary
from src.generalization_conservation_cellaxis_20261008.contracts import source_choice


def run(track,root_start=False):
    assert root_start and track in s.NEW_FIT_TRACKS
    prefit=prefit_check();resource_check()
    assert prefit['new_checkpoints']==s.NEW_CHECKPOINTS and prefit['source_only_configs']==s.CONFIGS
    folder=OUT/'crossed'/track;assert not (folder/'run_complete.json').exists()
    np,pd,old,_,predict=runtime()
    from src.generalization_crosscell_20261007.splits import outer_masks,inner_masks
    frame=load();x=features(track)
    assert values_hash(frame.measured_delta)==prefit['original_labels_sha256']
    predictions=[];chosen=[];inner=[];selection=[];folds=[]
    for task in s.TASKS:
        for fold in s.FOLDS:
            train,test=outer_masks(frame,task,fold);source=frame.loc[train].reset_index(drop=True)
            source_x=x[train];target=frame.loc[test].reset_index(drop=True);values=[]
            prefix=task+'__fold'+str(fold)
            for config in s.CONFIGS:
                oof=np.full(len(source),np.nan)
                for held in sorted(source.held_parent_fold.unique()):
                    tr,va=inner_masks(source,int(held));training=source.loc[tr].reset_index(drop=True)
                    model=fit(track,prefix+'__inner'+str(held),training,source_x[tr],config)
                    score=predict(model,source_x[va]);oof[va]=score
                    validation=source.loc[va].reset_index(drop=True)
                    value=old.inner_regret(validation,score)
                    inner.append({'task':task,'outer_fold':fold,'inner_fold':int(held),'configuration':config['id'],
                        'regret':value,'training_ids_sha256':rowhash(training),'training_rows':len(training),
                        'validation_rows':len(validation),'validation_ids_sha256':rowhash(validation),
                        'canonical_score_sha256':values_hash(score)})
                assert np.isfinite(oof).all()
                value=old.inner_regret(source,oof);values.append(value)
                selection.append({'task':task,'outer_fold':fold,'configuration':config['id'],
                                  'combined_source_oof_macro_regret':value,'canonical_oof_sha256':values_hash(oof)})
            config=source_choice(values);model=fit(track,prefix+'__outer',source,source_x,config)
            score=predict(model,x[test]);d=old.decisions(target,score,track)
            d['task']=task;d['gene_fold']=fold;chosen.append(d)
            predictions.extend({'track':track,'task':task,'gene_fold':fold,'intervention_id':row.intervention_id,
                                'score':float(score[i]),'configuration':config['id']} for i,row in enumerate(target.itertuples()))
            folds.append({'task':task,'fold':fold,'selected_configuration':config,
                'all_source_oof_scores':dict(zip([c['id'] for c in s.CONFIGS],values)),
                'training_identity':model['_identity'],'training_ids_sha256':rowhash(source),
                'test_ids_sha256':rowhash(target),'test_metadata_sha256':metadata_hash(target),
                'test_labels_sha256':values_hash(target.measured_delta),'test_rows':len(target)})
            print('RBP cell-axis',track,task,fold,'finished',flush=True)
    d=pd.concat(chosen,ignore_index=True)
    assert len(predictions)==s.ROWS and len({r['intervention_id'] for r in predictions})==s.ROWS
    assert len(inner)==36 and len(selection)==18 and len(folds)==6
    assert len(list((folder/'fits').glob('*.json')))==42
    csvsave(folder/'predictions.csv.gz',pd.DataFrame(predictions),True);csvsave(folder/'decisions.csv',d)
    csvsave(folder/'inner_folds.csv',pd.DataFrame(inner));csvsave(folder/'source_selection.csv',pd.DataFrame(selection))
    csvsave(folder/'comparison.csv',task_summary(d));jsave(folder/'folds.json',folds)
    prefit_check()
    jsave(folder/'run_complete.json',{'status':'PASS','track':track,'fit_files':42,'prediction_rows':s.ROWS,
        'decision_rows':len(d),'prefit_sha256':sha256(PREFIT),'new_fits':42,'checkpoint_creation_digests':True,
        'target_cell_for_selection':False,'independent_confirmation':False})


if __name__=='__main__':
    import sys
    run(sys.argv[1],'--root-start' in sys.argv[2:])
