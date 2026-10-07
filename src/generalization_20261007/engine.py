"""Training-only model selection; immutable fold checkpoints and complete choices."""
from .common import *
import importlib, sys
from scipy import sparse
from src.cross_assay_20260927.models import purge

def module(track):
    assert track in TRACKS
    return importlib.import_module('src.'+NS+'.route_'+track)

def features(track):
    path=ART/(track+'_features.npz')
    if track=='representation':
        return sparse.load_npz(path)
    with np.load(path) as z:
        return z['features'].astype(float)

def checkpoint(track,name,frame,x,config):
    path=OUT/track/'fits'/(name+'_'+config['id']+'.json')
    ids=hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()
    if path.exists():
        result=readj(path)
        assert result['_training_ids_sha256']==ids and result['_config']==config
        return result
    result=module(track).fit_model(frame,x,config)
    result['_training_ids_sha256']=ids
    result['_training_studies']=sorted(frame.dataset.unique())
    result['_training_components']=sorted(frame.biological_component.unique())
    result['_config']=config
    jsave(path,result)
    return result

def run(track):
    manifest=freeze_check()
    assert not (OUT/track/'run_complete.json').exists(),'Preserve completed track'
    frame,_=load();x=features(track);mod=module(track)
    assert x.shape[0]==len(frame)
    predictions=[];choices=[];folds=[];selection=[]
    for held in STUDIES:
        test=frame.dataset.eq(held).to_numpy()
        train=purge(frame,~test,test)
        source=frame.loc[train].reset_index(drop=True);source_x=x[train]
        scores=[]
        for ci,config in enumerate(mod.CONFIGS):
            per_source=[]
            for inner in sorted(source.dataset.unique()):
                validation=source.dataset.eq(inner).to_numpy()
                inner_train=purge(source,~validation,validation)
                tr=source.loc[inner_train].reset_index(drop=True)
                va=source.loc[validation].reset_index(drop=True)
                assert held not in set(tr.dataset) and inner not in set(tr.dataset)
                fit=checkpoint(track,held+'__inner__'+inner,tr,source_x[inner_train],config)
                score=mod.predict_model(fit,source_x[validation])
                value=inner_regret(va,score)
                per_source.append(value)
                selection.append({'outer_held':held,'inner_held':inner,'configuration':config['id'],
                    'regret':value,'training_rows':len(tr),'validation_rows':len(va),
                    'training_ids_sha256':fit['_training_ids_sha256']})
            scores.append(float(np.mean(per_source)))
            print(track,held,config['id'],'inner complete',flush=True)
        # Frozen numerical tolerance and grid order; no outer-target selection.
        best=min(scores)
        ci=next(i for i,v in enumerate(scores) if v<=best+1e-12)
        config=mod.CONFIGS[ci]
        fit=checkpoint(track,held+'__outer',source,source_x,config)
        target=frame.loc[test].reset_index(drop=True)
        score=mod.predict_model(fit,x[test])
        d=decisions(target,score,track)
        choices.append(d)
        predictions.extend({'track':track,'dataset':held,'intervention_id':row.intervention_id,
            'score':float(score[j]),'configuration':config['id']} for j,row in enumerate(target.itertuples()))
        folds.append({'held':held,'selected_configuration':config,'inner_macro_regret':scores[ci],
            'all_inner_scores':dict(zip([c['id'] for c in mod.CONFIGS],scores)),
            'training_studies':fit['_training_studies'],'training_components':fit['_training_components'],
            'training_ids_sha256':fit['_training_ids_sha256'],
            'test_ids_sha256':hashlib.sha256('|'.join(target.intervention_id).encode()).hexdigest(),
            'test_rows':len(target)})
        print(track,held,'outer prediction complete',flush=True)
    d=pd.concat(choices,ignore_index=True)
    csvsave(OUT/track/'decisions.csv',d)
    csvsave(OUT/track/'predictions.csv.gz',pd.DataFrame(predictions),True)
    csvsave(OUT/track/'inner_selection.csv',pd.DataFrame(selection))
    csvsave(OUT/track/'comparison.csv',summary(d))
    jsave(OUT/track/'folds.json',folds)
    jsave(OUT/track/'run_complete.json',{'status':'PASS','track':track,'prefit_manifest_sha256':sha256(OUT/'prefit_manifest.json'),
        'fit_files':len(list((OUT/track/'fits').glob('*.json'))),'prediction_rows':len(predictions),'decision_rows':len(d),
        'outer_target_selection':False,'independent_confirmation':False,'no_new_source_outcomes':True})
    print(track,'complete',flush=True)

if __name__=='__main__':
    run(sys.argv[1])
