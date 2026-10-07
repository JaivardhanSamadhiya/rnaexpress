"""Nested source-cell gene folds; target cell and genes never select settings."""
from .common import *
from .routes import module,row_weights
from .splits import outer_masks,inner_masks
import sys


def features(track):
    assert track in TRACKS
    with np.load(FEATURE_ART/(feature_track(track)+'_model_features.npz')) as archive: matrix=archive['features'].astype(float)
    assert matrix.shape==(13781,WIDTHS[track]) and np.isfinite(matrix).all()
    return matrix


def choose_configuration(configs,values):
    assert len(configs)==len(values) and np.isfinite(values).all()
    minimum=min(values)
    return next(config for config,value in zip(configs,values) if value<=minimum+1e-12)


def checkpoint(track,name,frame,matrix,config):
    path=OUT/track/'fits'/(name+'_'+config['id']+'.json')
    ids=hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()
    label_hash=hashlib.sha256(frame.measured_delta.to_numpy(float).tobytes()).hexdigest()
    metadata_hash=hashlib.sha256(frame[META].to_csv(index=False,lineterminator='\n').encode()).hexdigest()
    matrix_hash=hashlib.sha256(np.ascontiguousarray(matrix,dtype=np.float64).tobytes()).hexdigest()
    weights_hash=hashlib.sha256(row_weights(frame).tobytes()).hexdigest()
    prefit_hash=sha256(OUT/'prefit_manifest.json')
    if path.exists():
        sidecar=path.with_suffix('.sha256.json')
        assert sidecar.exists(),'Reject orphan checkpoint without creation SHA'
        recorded=readj(sidecar)
        assert recorded['sha256']==sha256(path),'Checkpoint content changed'
        assert recorded['prefit_manifest_sha256']==prefit_hash
        model=readj(path)
        assert model['_training_ids_sha256']==ids and model['_config']==config
        assert model['_training_effect_sha256']==label_hash and model['_prefit_manifest_sha256']==prefit_hash
        assert model['_training_metadata_sha256']==metadata_hash and model['_training_matrix_sha256']==matrix_hash
        assert model['training_weights_sha256']==weights_hash
        return model
    assert not path.with_suffix('.sha256.json').exists(),'Reject orphan sidecar'
    assert frame.cell_type.nunique()==1
    model=module(track).fit_model(frame,matrix,config)
    model.update({'_training_ids_sha256':ids,'_training_effect_sha256':label_hash,
        '_prefit_manifest_sha256':prefit_hash,'_config':config,'_track':track,
        '_training_metadata_sha256':metadata_hash,'_training_matrix_sha256':matrix_hash,
        '_training_cell':frame.cell_type.iloc[0],
        '_training_components':sorted(frame.biological_component.unique()),
        '_training_gene_folds':sorted(frame.held_parent_fold.unique())})
    jsave(path,model)
    jsave(path.with_suffix('.sha256.json'),{'sha256':sha256(path),'prefit_manifest_sha256':prefit_hash})
    return model


def run(track):
    freeze_check()
    assert track in TRACKS and not (OUT/track/'run_complete.json').exists()
    frame,_=load();matrix=features(track);mod=module(track)
    predictions=[];choices=[];folds=[];inner_rows=[];selection_rows=[]
    for task in TASKS:
        for fold in FOLDS:
            train,test=outer_masks(frame,task,fold)
            source=frame.loc[train].reset_index(drop=True);source_x=matrix[train]
            targets=frame.loc[test].reset_index(drop=True)
            values=[]
            name=task+'__fold'+str(fold)
            for config in mod.CONFIGS:
                held_predictions=np.full(len(source),np.nan)
                for inner in sorted(source.held_parent_fold.unique()):
                    tr,va=inner_masks(source,int(inner))
                    training=source.loc[tr].reset_index(drop=True)
                    fitted=checkpoint(track,name+'__inner'+str(inner),training,source_x[tr],config)
                    score=mod.predict_model(fitted,source_x[va]);held_predictions[va]=score
                    validation=source.loc[va].reset_index(drop=True)
                    inner_rows.append({'task':task,'outer_fold':fold,'inner_fold':int(inner),
                        'configuration':config['id'],'regret':inner_regret(validation,score),
                        'training_ids_sha256':fitted['_training_ids_sha256'],
                        'training_rows':int(tr.sum()),'validation_rows':int(va.sum())})
                assert np.isfinite(held_predictions).all()
                # Combining predictions first weights each component equally,
                # rather than weighting unequal-size gene folds equally.
                value=inner_regret(source,held_predictions);values.append(value)
                selection_rows.append({'task':task,'outer_fold':fold,'configuration':config['id'],
                    'combined_source_oof_macro_regret':value})
            config=choose_configuration(mod.CONFIGS,values)
            fitted=checkpoint(track,name+'__outer',source,source_x,config)
            score=mod.predict_model(fitted,matrix[test])
            d=decisions(targets,score,track);d['task']=task;d['gene_fold']=fold;choices.append(d)
            predictions.extend({'track':track,'task':task,'gene_fold':fold,'intervention_id':r.intervention_id,
                'score':float(score[i]),'configuration':config['id']} for i,r in enumerate(targets.itertuples()))
            folds.append({'task':task,'fold':fold,'selected_configuration':config,
                'all_source_oof_scores':dict(zip([c['id'] for c in mod.CONFIGS],values)),
                'training_ids_sha256':fitted['_training_ids_sha256'],
                'test_ids_sha256':hashlib.sha256('|'.join(targets.intervention_id).encode()).hexdigest(),
                'training_cell':fitted['_training_cell'],'training_components':fitted['_training_components'],
                'test_rows':len(targets)})
            print(track,task,'fold',fold,'complete',flush=True)
    d=pd.concat(choices,ignore_index=True)
    csvsave(OUT/track/'predictions.csv.gz',pd.DataFrame(predictions),True)
    csvsave(OUT/track/'decisions.csv',d)
    csvsave(OUT/track/'inner_folds.csv',pd.DataFrame(inner_rows))
    csvsave(OUT/track/'source_selection.csv',pd.DataFrame(selection_rows))
    csvsave(OUT/track/'comparison.csv',task_summary(d))
    jsave(OUT/track/'folds.json',folds)
    assert len(predictions)==13781 and len([p for p in (OUT/track/'fits').glob('*.json') if not p.name.endswith('.sha256.json')])==42
    jsave(OUT/track/'run_complete.json',{'status':'PASS','track':track,'fit_files':42,
        'prediction_rows':len(predictions),'decision_rows':len(d),
        'prefit_manifest_sha256':sha256(OUT/'prefit_manifest.json'),
        'target_cell_outcomes_for_selection':False,'independent_confirmation':False})


def task_summary(d):
    cols=['regret','wrong_direction','avoidable_wrong','pairwise_accuracy']
    return d.groupby(['model','task','biological_component'])[cols].mean().groupby(['model','task']).mean().reset_index()


if __name__=='__main__':run(sys.argv[1])
