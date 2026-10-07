"""Unchanged frozen pairwise objective; source-only grid and checked safe JSON."""
from .experiment_common import *
from types import SimpleNamespace
import os
import importlib,importlib.metadata
from threadpoolctl import threadpool_limits
from src.generalization_20261007.route_scaling import fit_model as frozen_fit,predict_model as frozen_predict
from src.cross_assay_20260927.models import row_weights,pair_indices

CONFIGS=[{'id':'pair_005','penalty':.005,'scaling':'pair'},
         {'id':'pair_05','penalty':.05,'scaling':'pair'},
         {'id':'pair_5','penalty':.5,'scaling':'pair'}]

def numerical_runtime_binding():
    base=(ROOT/'data/interim/mechanism_v2/runtime').resolve();files={}
    names=['numpy','numpy.core._multiarray_umath','scipy','scipy.optimize._optimize','scipy.optimize._lbfgsb_py',
           'scipy.optimize._lbfgsb','scipy.special._ufuncs','threadpoolctl']
    for name in names:
        path=Path(importlib.import_module(name).__file__).resolve();assert path.is_relative_to(base)
        files[path.relative_to(ROOT).as_posix()]=sha256(path)
    for directory in ('numpy.libs','scipy.libs'):
        for path in sorted((base/directory).glob('*.dll')):files[path.relative_to(ROOT).as_posix()]=sha256(path)
    versions={name:importlib.metadata.version(name) for name in ('numpy','scipy','threadpoolctl')}
    assert versions['numpy']=='1.26.4' and versions['scipy']=='1.14.1'
    return {'versions':versions,'files':files,'numerical_threads':1}

def pair_hash(frame):
    left,right,labels,weights,studies=pair_indices(frame.reset_index(drop=True))
    return hashlib.sha256(left.tobytes()+right.tobytes()+labels.tobytes()+weights.tobytes()+'|'.join(studies).encode()).hexdigest()

def validate_model(model):
    values=[np.asarray(model[name],dtype=float) for name in ('mean','scale','beta')]
    assert all(value.ndim==1 and np.isfinite(value).all() for value in values)
    assert len(values[0])==len(values[1])==len(values[2])
    assert (values[1]>0).all()
    assert np.all(values[2][~np.asarray(model['active'],bool)]==0)

def fit_model(frame,x,config):
    freeze_check(full=False)
    assert config in CONFIGS and frame.cell_type.nunique()==1
    for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):assert os.environ.get(name)=='1'
    with threadpool_limits(limits=1):model=frozen_fit(frame,x,config)
    model['training_weights_sha256']=hashlib.sha256(row_weights(frame).tobytes()).hexdigest()
    model['training_pair_roster_sha256']=pair_hash(frame)
    validate_model(model);return model

def predict_model(model,x):
    validate_model(model);return frozen_predict(model,x)

def independent_predict(model,x):
    validate_model(model)
    result=np.zeros(len(x),dtype=float)
    for j,coefficient in enumerate(model['beta']):
        result+=(np.asarray(x)[:,j]-model['mean'][j])/model['scale'][j]*coefficient
    return result

def module(track):
    assert track in TRACKS
    return SimpleNamespace(CONFIGS=CONFIGS,fit_model=fit_model,predict_model=predict_model,independent_predict=independent_predict)
