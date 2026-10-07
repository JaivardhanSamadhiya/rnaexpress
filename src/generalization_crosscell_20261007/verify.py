"""Independent inner/outer score replay and original-truth extreme decisions."""
from .common import *
from .engine import features,task_summary
from .routes import module
from .splits import outer_masks,inner_masks


def run():
    freeze_check();frame,_=load();max_error=0.;inner_count=0;outer_count=0;choices_checked=0
    for track in TRACKS:
        x=features(track);mod=module(track)
        p=pd.read_csv(OUT/track/'predictions.csv.gz',float_precision='round_trip')
        d=pd.read_csv(OUT/track/'decisions.csv',float_precision='round_trip')
        inner_saved=pd.read_csv(OUT/track/'inner_folds.csv',float_precision='round_trip')
        selected=pd.read_csv(OUT/track/'source_selection.csv',float_precision='round_trip')
        assert len(p)==len(frame) and p.intervention_id.is_unique and set(p.intervention_id)==set(frame.intervention_id)
        fold_roster=readj(OUT/track/'folds.json')
        assert len(fold_roster)==6
        assert {(r['task'],r['fold']) for r in fold_roster}=={(task,fold) for task in TASKS for fold in FOLDS}
        assert len(inner_saved)==36 and len(selected)==18
        for fold_info in fold_roster:
            task,fold=fold_info['task'],fold_info['fold'];tr,te=outer_masks(frame,task,fold)
            source=frame.loc[tr].reset_index(drop=True);source_x=x[tr]
            target=frame.loc[te].reset_index(drop=True);name=task+'__fold'+str(fold)
            source_scores=[]
            for config in mod.CONFIGS:
                scores=np.full(len(source),np.nan)
                for inner in sorted(source.held_parent_fold.unique()):
                    train,validation=inner_masks(source,int(inner))
                    training=source.loc[train].reset_index(drop=True)
                    m=readj(OUT/track/'fits'/(name+'__inner'+str(inner)+'_'+config['id']+'.json'))
                    check_model(m,training,config,track)
                    inner_score=mod.predict_model(m,source_x[validation])
                    scores[validation]=inner_score;inner_count+=1
                    recorded=inner_saved[inner_saved.task.eq(task)&inner_saved.outer_fold.eq(fold)&
                        inner_saved.inner_fold.eq(inner)&inner_saved.configuration.eq(config['id'])]
                    assert len(recorded)==1
                    assert abs(float(recorded.regret.iloc[0])-replay_regret(source.loc[validation].reset_index(drop=True),inner_score))<1e-12
                    assert recorded.training_ids_sha256.iloc[0]==m['_training_ids_sha256']
                    assert int(recorded.training_rows.iloc[0])==int(train.sum())
                    assert int(recorded.validation_rows.iloc[0])==int(validation.sum())
                assert np.isfinite(scores).all()
                value=replay_regret(source,scores);source_scores.append(value)
                row=selected[selected.task.eq(task)&selected.outer_fold.eq(fold)&selected.configuration.eq(config['id'])]
                assert len(row)==1 and abs(float(row.combined_source_oof_macro_regret.iloc[0])-value)<1e-12
                assert abs(fold_info['all_source_oof_scores'][config['id']]-value)<1e-12
            minimum=min(source_scores)
            config=next(c for c,v in zip(mod.CONFIGS,source_scores) if v<=minimum+1e-12)
            assert config==fold_info['selected_configuration']
            m=readj(OUT/track/'fits'/(name+'__outer_'+config['id']+'.json'))
            check_model(m,source,config,track);outer_count+=1
            assert hashlib.sha256('|'.join(source.intervention_id).encode()).hexdigest()==fold_info['training_ids_sha256']
            assert hashlib.sha256('|'.join(target.intervention_id).encode()).hexdigest()==fold_info['test_ids_sha256']
            score=mod.predict_model(m,x[te])
            saved=p[p.task.eq(task)&p.gene_fold.eq(fold)].set_index('intervention_id').loc[target.intervention_id]
            error=float(np.max(abs(score-saved.score.to_numpy())));assert error<1e-9;max_error=max(max_error,error)
            check_choices(target,score,d[d.task.eq(task)&d.gene_fold.eq(fold)])
            choices_checked+=2*target.parent_context_id.nunique()
        assert len(list((OUT/track/'fits').glob('*.json')))==42
        actual=task_summary(d).sort_values('task').reset_index(drop=True)
        saved=pd.read_csv(OUT/track/'comparison.csv',float_precision='round_trip').sort_values('task').reset_index(drop=True)
        np.testing.assert_allclose(actual[['regret','wrong_direction','avoidable_wrong','pairwise_accuracy']],
            saved[['regret','wrong_direction','avoidable_wrong','pairwise_accuracy']],atol=1e-12,rtol=0)
        print('Verified',track,flush=True)
    assert inner_count==252 and outer_count==42
    jsave(OUT/'verification_receipt.json',{'status':'PASS','inner_models_replayed':inner_count,
        'outer_models_replayed':outer_count,'all_models':inner_count+outer_count,
        'candidate_scores_replayed':len(frame)*len(TRACKS),'maximum_score_error':max_error,
        'original_truth_choices_regrets_checked':choices_checked,'source_only_selection_checked':True,
        'gene_and_exact_allele_exclusions_checked':True,'independent_confirmation':False})


def check_model(model,training,config,track):
    assert model['_config']==config and model['_track']==track
    assert model['_training_ids_sha256']==hashlib.sha256('|'.join(training.intervention_id).encode()).hexdigest()
    assert model['_training_effect_sha256']==hashlib.sha256(training.measured_delta.to_numpy(float).tobytes()).hexdigest()
    assert model['_prefit_manifest_sha256']==sha256(OUT/'prefit_manifest.json')
    assert training.cell_type.nunique()==1 and model['_training_cell']==training.cell_type.iloc[0]
    assert model['_training_components']==sorted(training.biological_component.unique())
    assert model['_training_gene_folds']==sorted(training.held_parent_fold.unique())


def replay_regret(frame,score):
    """Independent source-selection arithmetic, without engine decision helpers."""
    data=frame[['intervention_id','parent_context_id','biological_component','measured_delta']].copy()
    data['score']=np.asarray(score)
    assert len(score)==len(data) and np.isfinite(score).all()
    bounds=data.groupby('parent_context_id').measured_delta.agg(['min','max'])
    assert ((bounds['max']-bounds['min'])>0).all()
    pieces=[]
    for direction in (-1,1):
        chosen=data.assign(utility=direction*data.score).sort_values(
            ['parent_context_id','utility','intervention_id'],ascending=[True,False,True]).drop_duplicates('parent_context_id')
        limits=bounds.loc[chosen.parent_context_id]
        best=limits['max'].to_numpy() if direction==1 else -limits['min'].to_numpy()
        selected=direction*chosen.measured_delta.to_numpy()
        pieces.append(pd.DataFrame({'biological_component':chosen.biological_component.to_numpy(),
            'regret':(best-selected)/(limits['max']-limits['min']).to_numpy()}))
    return float(pd.concat(pieces,ignore_index=True).groupby('biological_component').regret.mean().mean())


def check_choices(target,score,saved):
    joined=target[['intervention_id','parent_context_id','measured_delta']].copy();joined['score']=score
    for direction in (-1,1):
        selected=joined.assign(utility=direction*joined.score).sort_values(
            ['parent_context_id','utility','intervention_id'],ascending=[True,False,True]).drop_duplicates('parent_context_id').set_index('parent_context_id')
        actual=saved[saved.direction.eq(direction)].set_index('parent_context_id').loc[selected.index]
        assert list(actual.selected_id)==list(selected.intervention_id)
        bounds=joined.groupby('parent_context_id').measured_delta.agg(['min','max']).loc[selected.index]
        best=bounds['max'].to_numpy() if direction==1 else -bounds['min'].to_numpy()
        effect=direction*selected.measured_delta.to_numpy();regret=(best-effect)/(bounds['max']-bounds['min']).to_numpy()
        np.testing.assert_allclose(regret,actual.regret,atol=1e-12,rtol=0)
        np.testing.assert_array_equal(effect<-1e-12,actual.wrong_direction.astype(bool))
        np.testing.assert_array_equal((effect<-1e-12)&(best>1e-12),actual.avoidable_wrong.astype(bool))


if __name__=='__main__':run()
