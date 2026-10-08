"""Reuse old exact source controls; full replay, no refit or retro-birth claim."""
from .common import *
from .checkpoints import verify_numerics
from .numeric import canonical,regret,decisions,equal_decisions
from src.generalization_conservation_cellaxis_20261008.contracts import source_choice


def old_inputs():
    np,pd,old,*_=runtime();committed(OLD_OUT/'prefit_manifest.json')
    committed(NUMERIC_AUDIT);audit=readj(NUMERIC_AUDIT)
    assert audit['status']=='PASS' and audit['inner_checkpoints_checked']==252 and audit['outer_checkpoints_checked']==42
    assert audit['models_fit']==0 and audit['source_rows']==s.ROWS and audit['numerical_threads']==1
    assert audit['prefit_manifest_sha256']==sha256(OLD_OUT/'prefit_manifest.json')
    libraries=audit['loaded_numeric_libraries']
    assert np.__version__==libraries['numpy_version'] and pd.__version__==libraries['pandas_version']
    assert sha256(np.__file__)==libraries['numpy_init_sha256'] and sha256(pd.__file__)==libraries['pandas_init_sha256']
    assert old.TASKS==s.TASKS and old.FOLDS==s.FOLDS
    from src.generalization_crosscell_20261007.routes import CONFIGS
    assert CONFIGS==s.CONFIGS
    committed(OLD_KNOWN/'evaluation_manifest.json')
    known=readj(OLD_KNOWN/'verification_receipt.json');assert known['status']=='PASS'
    assert known['same_checkpoint_both_states_verified'] and known['crossed_state_predictors_rechecked']==42
    assert known['evaluation_manifest_sha256']==sha256(OLD_KNOWN/'evaluation_manifest.json')
    for track in s.REUSED_CONTROLS:
        for filename in ('predictions.csv.gz','decisions.csv','comparison.csv','roster.json','complete.json'):
            path=OLD_KNOWN/track/filename;name=path.relative_to(ROOT).as_posix()
            assert sha256(path)==known['result_files'][name],name
    paired=readj(OLD_KNOWN/'canonical_paired_state_contrast.json')
    assert paired['status']=='DESCRIPTIVE' and paired['predictor_calls']==42 and paired['all_paired_feature_bytes_equal']
    assert paired['main_gate_and_original_id_policy_unchanged'] and paired['selects_nothing']
    assert paired['evaluation_manifest_sha256']==sha256(OLD_KNOWN/'evaluation_manifest.json')
    return audit,known


def selected_model(track,task,fold,frame,x):
    assert track in s.REUSED_CONTROLS
    from src.generalization_crosscell_20261007.splits import outer_masks
    from src.generalization_crosscell_20261007.verify import check_model
    np,pd,*_=runtime();roster=readj(OLD_OUT/track/'folds.json')
    assert len(roster)==6 and {(r['task'],r['fold']) for r in roster}=={(t,f) for t in s.TASKS for f in s.FOLDS}
    info=next(r for r in roster if (r['task'],r['fold'])==(task,fold))
    table=pd.read_csv(OLD_OUT/track/'source_selection.csv',float_precision='round_trip');values=[]
    for config in s.CONFIGS:
        row=table[table.task.eq(task)&table.outer_fold.eq(fold)&table.configuration.eq(config['id'])]
        assert len(row)==1;values.append(float(row.iloc[0].combined_source_oof_macro_regret))
    config=source_choice(values);assert config==info['selected_configuration']
    train,test=outer_masks(frame,task,fold);source=frame.loc[train].reset_index(drop=True)
    assert rowhash(source)==info['training_ids_sha256'] and rowhash(frame.loc[test])==info['test_ids_sha256']
    path=OLD_OUT/track/'fits'/(task+'__fold'+str(fold)+'__outer_'+config['id']+'.json')
    model=readj(path);check_model(model,source,config,track);verify_numerics(model,source,x[train],config)
    return model,config,train,test,path


def replay(track,frame,x):
    np,pd,*_=runtime()
    from src.generalization_crosscell_20261007.splits import outer_masks,inner_masks
    from src.generalization_crosscell_20261007.verify import check_model
    audit,_=old_inputs();assert values_hash(frame.measured_delta)==audit['mean_effect_float64_sha256']
    assert rowhash(frame)==audit['original_mikl_row_ids_sha256']
    inputs=input_check();name=inputs['feature_paths'][track]
    assert sha256(ROOT/name)==audit['observed_input_sha256'][name]
    selected=pd.read_csv(OLD_OUT/track/'source_selection.csv',float_precision='round_trip')
    inner=pd.read_csv(OLD_OUT/track/'inner_folds.csv',float_precision='round_trip')
    predictions=pd.read_csv(OLD_OUT/track/'predictions.csv.gz',float_precision='round_trip')
    saved=pd.read_csv(OLD_OUT/track/'decisions.csv',float_precision='round_trip')
    assert len(selected)==18 and len(inner)==36 and len(predictions)==s.ROWS and predictions.intervention_id.is_unique
    assert set(predictions.intervention_id)==set(frame.intervention_id) and set(predictions.track)==set(saved.model)=={track}
    records=[];inner_count=0;outer_count=0;maximum=0.
    for task in s.TASKS:
        for fold in s.FOLDS:
            train,test=outer_masks(frame,task,fold);source=frame.loc[train].reset_index(drop=True);source_x=x[train]
            values=[];prefix=task+'__fold'+str(fold)
            for config in s.CONFIGS:
                oof=np.full(len(source),np.nan)
                for held in sorted(source.held_parent_fold.unique()):
                    tr,va=inner_masks(source,int(held));training=source.loc[tr].reset_index(drop=True)
                    path=OLD_OUT/track/'fits'/(prefix+'__inner'+str(held)+'_'+config['id']+'.json')
                    assert sha256(path)==audit['observed_input_sha256'][path.relative_to(ROOT).as_posix()]
                    model=readj(path);check_model(model,training,config,track);pair=verify_numerics(model,training,source_x[tr],config)
                    score,error=canonical(model,source_x[va]);maximum=max(maximum,error);oof[va]=score
                    value=regret(source.loc[va].reset_index(drop=True),score)
                    row=inner[inner.task.eq(task)&inner.outer_fold.eq(fold)&inner.inner_fold.eq(held)&inner.configuration.eq(config['id'])]
                    assert len(row)==1 and abs(float(row.iloc[0].regret)-value)<1e-12
                    assert row.iloc[0].training_ids_sha256==rowhash(training)
                    records.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(path),
                        'training_ids_sha256':rowhash(training),'training_effects_sha256':values_hash(training.measured_delta),
                        'training_features_sha256':values_hash(source_x[tr]),'pair_identity':pair,'independent_error':error})
                    inner_count+=1
                assert np.isfinite(oof).all();value=regret(source,oof);values.append(value)
                row=selected[selected.task.eq(task)&selected.outer_fold.eq(fold)&selected.configuration.eq(config['id'])]
                assert len(row)==1 and abs(float(row.iloc[0].combined_source_oof_macro_regret)-value)<1e-12
            model,config,_,_,path=selected_model(track,task,fold,frame,x)
            assert config==source_choice(values) and sha256(path)==audit['observed_input_sha256'][path.relative_to(ROOT).as_posix()]
            score,error=canonical(model,x[test]);maximum=max(maximum,error);target=frame.loc[test].reset_index(drop=True)
            observed=predictions[predictions.task.eq(task)&predictions.gene_fold.eq(fold)].set_index('intervention_id').loc[target.intervention_id]
            assert set(observed.configuration)=={config['id']};np.testing.assert_allclose(score,observed.score,atol=1e-9,rtol=0)
            equal_decisions(decisions(target,score),saved[saved.task.eq(task)&saved.gene_fold.eq(fold)])
            records.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(path),
                'training_ids_sha256':rowhash(source),'training_features_sha256':values_hash(x[train]),'independent_error':error})
            outer_count+=1
    assert inner_count==36 and outer_count==6 and len(list((OLD_OUT/track/'fits').glob('*.json')))==42
    return {'track':track,'inner':inner_count,'outer':outer_count,'maximum_error':maximum,'checkpoints':records}


def prepare(root_start=False):
    design_check(root_start);thread_check();resource_check();assert not (OUT/'control_reuse_receipt.json').exists()
    from src.generalization_20261007.verify import preservation
    preservation()
    inputs=input_check();frame=load();old_inputs();records=[];files={}
    for track in s.REUSED_CONTROLS:
        records.append(replay(track,frame,features(track)))
        for folder in (OLD_OUT/track,OLD_KNOWN/track):
            for path in folder.rglob('*'):
                if path.is_file():files[path.relative_to(ROOT).as_posix()]=sha256(path)
    for path in (NUMERIC_AUDIT,OLD_OUT/'prefit_manifest.json',OLD_OUT/'verification_receipt.json',
                 OLD_KNOWN/'evaluation_manifest.json',OLD_KNOWN/'verification_receipt.json',
                 OLD_KNOWN/'canonical_paired_state_contrast.json',OLD_KNOWN/'exact_menu_pairs.csv'):
        files[path.relative_to(ROOT).as_posix()]=sha256(path)
    preservation()
    jsave(OUT/'control_reuse_receipt.json',{'status':'PASS','files':files,'tracks':records,
        'original_labels_sha256':values_hash(frame.measured_delta),'row_ids_sha256':rowhash(frame),
        'metadata_sha256':metadata_hash(frame),'array_receipt_sha256':sha256(PREP_OUT/'array_receipt.json'),
        'design_manifest_sha256':sha256(DESIGN),'all_inner_source_configs_reselected':True,
        'actual_training_pair_scaling_checked':True,'canonical_original_full_shape_scores_checked':True,
        'observed_checkpoint_bytes_not_creation_time_proof':True,'new_control_fits':0})


def check():
    receipt=readj(OUT/'control_reuse_receipt.json');assert receipt['status']=='PASS'
    assert receipt['array_receipt_sha256']==sha256(PREP_OUT/'array_receipt.json')
    assert receipt['design_manifest_sha256']==sha256(DESIGN)
    assert receipt['new_control_fits']==0 and receipt['observed_checkpoint_bytes_not_creation_time_proof']
    assert {r['track'] for r in receipt['tracks']}==set(s.REUSED_CONTROLS)
    assert all(r['inner']==36 and r['outer']==6 for r in receipt['tracks'])
    hash_files(receipt['files']);return receipt


if __name__=='__main__':
    import sys
    prepare('--root-start' in sys.argv[1:])
