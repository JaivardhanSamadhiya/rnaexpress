"""Certify exact existing feature references and outcome-free split bindings."""
from .experiment_common import *
from .splits import outer_masks,inner_masks
from .graph import runtime_binding
from .routes import numerical_runtime_binding

def run():
    from src.generalization_20261007.verify import preservation
    preservation();assert not any((OUT/track/'fits').exists() for track in TRACKS)
    upstream=UNPURGED_OUT/'prefit_manifest.json';manifest=readj(upstream)
    assert subprocess.check_output(['git','show','HEAD:'+upstream.relative_to(ROOT).as_posix()],cwd=ROOT)==upstream.read_bytes()
    frame,_=load(False)
    assert len(frame)==13781 and frame.similarity_component.nunique()==184
    original=pd.read_csv(UNPURGED_OUT/'row_index.csv.gz',usecols=['intervention_id'])
    assert list(frame.intervention_id)==list(original.intervention_id)
    paths={track:FEATURE_ART/(track+'_model_features.npz') for track in TRACKS}
    base=None
    for track,path in paths.items():
        assert sha256(path)==manifest['files'][path.relative_to(ROOT).as_posix()]
        with np.load(path) as archive:x=archive['features'].astype(float)
        assert x.shape==(len(frame),WIDTHS[track]) and np.isfinite(x).all()
        if track=='simple':simple=x.copy()
        elif track=='base':base=x.copy();np.testing.assert_array_equal(base[:,:102],simple)
        else:np.testing.assert_array_equal(x[:,:246],base)
    rosters=[]
    for task in TASKS:
        for fold in FOLDS:
            tr,te=outer_masks(frame,task,fold);source=frame.loc[tr].reset_index(drop=True)
            assert tr.any() and te.any() and set(source.held_parent_fold)==set(FOLDS)-{fold}
            for scope,inner,training,validation in [('outer',None,source,frame.loc[te])]+[
                ('inner',inner,source.loc[inner_masks(source,inner)[0]],source.loc[inner_masks(source,inner)[1]]) for inner in FOLDS if inner!=fold]:
                assert len(training) and len(validation)
                assert not set(training.similarity_component)&set(validation.similarity_component)
                rosters.append({'scope':scope,'task':task,'outer_fold':fold,'inner_fold':inner,
                    'training_rows':len(training),'validation_rows':len(validation),
                    'training_ids_sha256':hashlib.sha256('|'.join(training.intervention_id).encode()).hexdigest(),
                    'validation_ids_sha256':hashlib.sha256('|'.join(validation.intervention_id).encode()).hexdigest(),
                    'training_metadata_sha256':hashlib.sha256(training[META].to_csv(index=False,lineterminator='\n').encode()).hexdigest()})
    csvsave(OUT/'supervised_row_index.csv.gz',frame,True)
    csvsave(OUT/'supervised_split_rosters.csv',pd.DataFrame(rosters))
    jsave(OUT/'numerical_runtime_binding.json',numerical_runtime_binding())
    jsave(OUT/'feature_admission_receipt.json',{'status':'PASS','outcome_columns_read':False,'project_fits':0,
        'tracks':TRACKS,'widths':WIDTHS,'rows':len(frame),'rosters':len(rosters),
        'row_ids_sha256':hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest(),
        'upstream_manifest_sha256':sha256(upstream),'graph_receipt_sha256':sha256(OUT/'metadata_graph_receipt.json'),
        'feature_files':{path.relative_to(ROOT).as_posix():sha256(path) for path in paths.values()},
        'native_distance_runtime':runtime_binding(),'checkpoint_adoption':False})
    print('Seven feature references/18 similarity-purged source rosters admitted; no fit',flush=True)

if __name__=='__main__':run()
