"""Replay all144 new inner24outer plus exact84old controls, never fit."""
from .common import *
from .numeric import canonical,decisions,equal_decisions,regret,task_summary
from .checkpoints import identity,checked,verify_numerics
from src.generalization_rbp_cellaxis_20261007.contracts import source_choice


def prediction_roster(p,d,frame,track,tasks):
    assert len(p)==s.ROWS and p.intervention_id.is_unique and set(p.intervention_id)==set(frame.intervention_id)
    assert set(p.track)==set(d.model)=={track} and set(p.task)==set(d.task)==set(tasks)
    assert set(p.gene_fold)==set(d.gene_fold)==set(s.FOLDS)
    assert set(d.dataset)=={'mikl_gse173098'}
    assert not d.duplicated(['task','gene_fold','parent_context_id','direction']).any()
    expected={(r.parent_context_id,direction) for r in frame.itertuples() for direction in (-1,1)}
    assert set(zip(d.parent_context_id,d.direction))==expected and len(d)==len(expected)


def run(root_start=False):
    assert root_start;prefit=prefit_check();frame=load();np,pd,*_=runtime()
    assert values_hash(frame.measured_delta)==prefit['original_labels_sha256']
    from src.generalization_crosscell_20261007.splits import outer_masks,inner_masks
    from .controls import replay as control_replay
    assert not (OUT/'crossed_verification_receipt.json').exists()
    counts={'inner':0,'outer':0};maximum=0.;saved_maximum=0.;files={};control_records=[]
    for track in s.REUSED_CONTROLS:
        control_records.append(control_replay(track,frame,features(track)))
    for track in s.NEW_FIT_TRACKS:
        x=features(track);folder=OUT/'crossed'/track;complete=readj(folder/'run_complete.json')
        assert complete['status']=='PASS' and complete['fit_files']==42 and complete['prefit_sha256']==sha256(PREFIT)
        p=pd.read_csv(folder/'predictions.csv.gz',float_precision='round_trip')
        d=pd.read_csv(folder/'decisions.csv',float_precision='round_trip');prediction_roster(p,d,frame,track,s.TASKS)
        inner=pd.read_csv(folder/'inner_folds.csv',float_precision='round_trip')
        selection=pd.read_csv(folder/'source_selection.csv',float_precision='round_trip')
        roster=readj(folder/'folds.json')
        assert len(inner)==36 and len(selection)==18 and len(roster)==6
        assert {(r['task'],r['fold']) for r in roster}=={(t,f) for t in s.TASKS for f in s.FOLDS}
        for task in s.TASKS:
            for fold in s.FOLDS:
                tr,te=outer_masks(frame,task,fold);source=frame.loc[tr].reset_index(drop=True);source_x=x[tr]
                target=frame.loc[te].reset_index(drop=True);values=[];prefix=task+'__fold'+str(fold)
                info=next(r for r in roster if (r['task'],r['fold'])==(task,fold))
                assert info['test_ids_sha256']==rowhash(target) and info['test_metadata_sha256']==metadata_hash(target)
                assert info['test_labels_sha256']==values_hash(target.measured_delta) and info['test_rows']==len(target)
                for config in s.CONFIGS:
                    oof=np.full(len(source),np.nan)
                    for held in sorted(source.held_parent_fold.unique()):
                        it,iv=inner_masks(source,int(held));training=source.loc[it].reset_index(drop=True)
                        path=folder/'fits'/(prefix+'__inner'+str(held)+'_'+config['id']+'.json')
                        model=checked(path,identity(track,training,source_x[it],config),config)
                        verify_numerics(model,training,source_x[it],config)
                        score,error=canonical(model,source_x[iv]);oof[iv]=score;maximum=max(maximum,error)
                        validation=source.loc[iv].reset_index(drop=True);value=regret(validation,score)
                        row=inner[inner.task.eq(task)&inner.outer_fold.eq(fold)&inner.inner_fold.eq(held)&inner.configuration.eq(config['id'])]
                        assert len(row)==1 and abs(float(row.iloc[0].regret)-value)<1e-12
                        assert row.iloc[0].training_ids_sha256==rowhash(training) and row.iloc[0].validation_ids_sha256==rowhash(validation)
                        assert int(row.iloc[0].training_rows)==len(training) and int(row.iloc[0].validation_rows)==len(validation)
                        assert row.iloc[0].canonical_score_sha256==values_hash(score);counts['inner']+=1
                    assert np.isfinite(oof).all();value=regret(source,oof);values.append(value)
                    row=selection[selection.task.eq(task)&selection.outer_fold.eq(fold)&selection.configuration.eq(config['id'])]
                    assert len(row)==1 and abs(float(row.iloc[0].combined_source_oof_macro_regret)-value)<1e-12
                    assert row.iloc[0].canonical_oof_sha256==values_hash(oof)
                    assert abs(info['all_source_oof_scores'][config['id']]-value)<1e-12
                config=source_choice(values);assert config==info['selected_configuration']
                path=folder/'fits'/(prefix+'__outer_'+config['id']+'.json')
                model=checked(path,identity(track,source,source_x,config),config)
                assert model['_identity']==info['training_identity'] and info['training_ids_sha256']==rowhash(source)
                verify_numerics(model,source,source_x,config);score,error=canonical(model,x[te]);maximum=max(maximum,error)
                observed=p[p.task.eq(task)&p.gene_fold.eq(fold)].set_index('intervention_id').loc[target.intervention_id]
                assert set(observed.configuration)=={config['id']}
                saved_error=float(np.max(abs(score-observed.score.to_numpy(float))));assert saved_error<1e-9
                saved_maximum=max(saved_maximum,saved_error)
                equal_decisions(decisions(target,score),d[d.task.eq(task)&d.gene_fold.eq(fold)]);counts['outer']+=1
        assert len(list((folder/'fits').glob('*.json')))==42 and complete['decision_rows']==len(d)
        np.testing.assert_allclose(d.wrong_direction,d.avoidable_wrong+d.unavoidable_wrong+d.neutral_only_alternative_wrong,atol=1e-12,rtol=0)
        actual=task_summary(d).sort_values('task').reset_index(drop=True)
        stored=pd.read_csv(folder/'comparison.csv',float_precision='round_trip').sort_values('task').reset_index(drop=True)
        pd.testing.assert_frame_equal(actual,stored,check_exact=False,atol=1e-12,rtol=0)
        for path in folder.rglob('*'):
            if path.is_file():files[path.relative_to(ROOT).as_posix()]=sha256(path)
        print('RBP crossed independent replay',track,'PASS',flush=True)
        del x
    assert counts=={'inner':144,'outer':24};prefit_check()
    jsave(OUT/'crossed_verification_receipt.json',{'status':'PASS','prefit_sha256':sha256(PREFIT),
        'new_inner_replayed':144,'new_outer_replayed':24,'reused_control_replays':control_records,
        'maximum_independent_arithmetic_error':maximum,'maximum_saved_score_error':saved_maximum,
        'files':files,'source_configs_independently_reselected':True,'checkpoint_birth_hashes_checked':True,
        'all_original_truth_choices_error_categories_pair_credit_recovery_checked':True,
        'canonical_exact_ID_ties_preserved':True,'models_fit':0,'independent_confirmation':False})


if __name__=='__main__':
    import sys
    run('--root-start' in sys.argv[1:])
