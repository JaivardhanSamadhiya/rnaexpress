"""Creation-byte new checkpoints and exact old training/scale contracts."""
from .common import *


def pair_identity(frame,x):
    np,_,_,_,_=runtime()
    from src.cross_assay_20260927.models import pair_indices,row_weights,scaler
    from src.generalization_20261007.route_scaling import pair_rms
    left,right,labels,weights,studies=pair_indices(frame.reset_index(drop=True))
    assert len(labels)
    h=hashlib.sha256()
    for value,dtype in ((left,'<i8'),(right,'<i8'),(labels,'<f8'),(weights,'<f8')):
        array=np.ascontiguousarray(value,dtype=dtype);h.update(str(array.shape).encode());h.update(array.tobytes())
    mean,candidate_scale=scaler(x,row_weights(frame))
    rms=pair_rms(x,left,right,weights)
    return {'pair_roster_labels_weights_sha256':h.hexdigest(),'training_pairs':len(labels)},mean,candidate_scale,rms


def verify_numerics(model,frame,x,config):
    np,*_=runtime();pair,mean,candidate_scale,rms=pair_identity(frame,x)
    assert model['config']==config and model['training_rows']==len(frame) and model['training_pairs']==pair['training_pairs']
    assert len(model['beta'])==len(model['mean'])==len(model['scale'])==x.shape[1]
    for name,expected in (('mean',mean),('candidate_scale',candidate_scale),('pair_rms',rms)):
        np.testing.assert_allclose(model[name],expected,atol=1e-12,rtol=0)
    scale=rms.copy();scale[scale<1e-8]=1.
    np.testing.assert_allclose(model['scale'],scale,atol=1e-12,rtol=0)
    np.testing.assert_array_equal(model['active'],rms>=1e-8)
    beta=np.asarray(model['beta'],dtype=float);assert np.isfinite(beta).all()
    assert np.all(beta[~(rms>=1e-8)]==0)
    assert model['training_studies']==['mikl_gse173098']
    assert model['training_components']==sorted(frame.biological_component.unique().tolist())
    return pair


def identity(track,frame,x,config):
    source=input_check();pair,*_=pair_identity(frame,x)
    return {'track':track,'configuration':config,'training_ids_sha256':rowhash(frame),
        'training_metadata_sha256':metadata_hash(frame),'training_effects_sha256':values_hash(frame.measured_delta),
        'training_features_sha256':values_hash(x),'training_rows':len(frame),'feature_columns':x.shape[1],
        'training_cell':frame.cell_type.iloc[0],'training_components':sorted(frame.biological_component.unique()),
        'training_gene_folds':sorted(frame.held_parent_fold.unique().tolist()),
        'source_npz_sha256':source['files'][source['feature_paths'][track]],'core_sha256':sha256(CORE),
        'prefit_sha256':sha256(PREFIT),'pair_identity':pair,'numerical_threads':1,
        'fitter_sha256':sha256(ROOT/'src/generalization_20261007/route_scaling.py'),
        'solver_sha256':sha256(ROOT/'src/cross_assay_20260927/models.py'),
        'endpoint_alignment':False,'original_truth_untransformed':True}


def checked(path,expected,config):
    path=Path(path);sidecar=path.with_suffix('.sha256')
    assert path.exists() and sidecar.exists() and sidecar.read_text().strip()==sha256(path)
    model=readj(path);assert model['_identity']==clean(expected) and model['config']==config
    return model


def fit(track,name,frame,x,config):
    assert track in s.NEW_FIT_TRACKS and frame.cell_type.nunique()==1
    assert config in s.CONFIGS
    path=OUT/'crossed'/track/'fits'/(name+'_'+config['id']+'.json');expected=identity(track,frame,x,config)
    if path.exists():return checked(path,expected,config)
    assert not path.with_suffix('.sha256').exists(),'Orphan creation digest'
    resource_check();np,_,_,fitter,_=runtime();result=fitter(frame,x,config)
    verify_numerics(result,frame,x,config);result['_identity']=expected
    jsave(path,result);save(path.with_suffix('.sha256'),(sha256(path)+'\n').encode())
    return result
