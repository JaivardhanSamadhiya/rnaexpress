"""Source-standardized weighted pointwise ridge, matched squared-error loss."""
import os
import hashlib
from .common import np
from .routes import row_weights

CONFIGS=[{'id':'ridge_005','alpha':.005},{'id':'ridge_05','alpha':.05},{'id':'ridge_5','alpha':.5}]
SUPPORT_CUTOFF=1e-12


def fit_model(frame,matrix,config):
    from .common import freeze_check
    freeze_check()
    assert config in CONFIGS and frame.cell_type.nunique()==1
    for variable in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
        assert os.environ.get(variable)=='1',variable
    x=np.asarray(matrix,dtype=np.float64);y=frame.measured_delta.to_numpy(float)
    assert x.ndim==2 and len(x)==len(y) and np.isfinite(x).all() and np.isfinite(y).all()
    weights=row_weights(frame);n=len(y)
    mean=np.average(x,axis=0,weights=weights)
    centered=x-mean
    rms=np.sqrt(np.average(centered**2,axis=0,weights=weights))
    supported=rms>SUPPORT_CUTOFF
    scale=np.where(supported,rms,1.)
    z=centered/scale;z[:,~supported]=0.
    intercept=float(np.average(y,weights=weights))
    beta=np.zeros(x.shape[1])
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        if supported.any():
            design=z[:,supported]
            gram=design.T@(weights[:,None]*design)/n
            rhs=design.T@(weights*(y-intercept))/n
            beta[supported]=np.linalg.solve(gram+config['alpha']*np.eye(len(rhs)),rhs)
    model={'kind':'weighted_pointwise_ridge_json_v1','width':x.shape[1],
        'mean':mean.tolist(),'scale':scale.tolist(),'raw_rms':rms.tolist(),
        'supported':supported.tolist(),'beta':beta.tolist(),'intercept':intercept,
        'alpha':config['alpha'],'support_cutoff':SUPPORT_CUTOFF,
        'training_weights_sha256':hashlib.sha256(weights.tobytes()).hexdigest(),
        'training_weights_mean':float(weights.mean())}
    direct=intercept+z@beta;replay=predict_model(model,x)
    error=float(np.max(np.abs(direct-replay)));assert error<1e-9
    model['native_export_max_error']=error
    return model


def validate_model(model):
    assert model['kind']=='weighted_pointwise_ridge_json_v1'
    assert model['support_cutoff']==SUPPORT_CUTOFF and model['alpha'] in (.005,.05,.5)
    assert np.isfinite(model['intercept'])
    for field in ('mean','scale','raw_rms','supported','beta'):assert len(model[field])==model['width']
    for field in ('mean','scale','raw_rms','beta'):assert np.isfinite(model[field]).all()
    assert (np.asarray(model['scale'])>0).all()
    support=np.asarray(model['supported'],dtype=bool)
    np.testing.assert_array_equal(support,np.asarray(model['raw_rms'])>SUPPORT_CUTOFF)
    np.testing.assert_array_equal(np.asarray(model['beta'])[~support],0.)
    np.testing.assert_array_equal(np.asarray(model['scale'])[~support],1.)


def predict_model(model,matrix):
    validate_model(model)
    x=np.asarray(matrix,dtype=np.float64)
    assert x.ndim==2 and x.shape[1]==model['width'] and np.isfinite(x).all()
    z=(x-np.asarray(model['mean']))/np.asarray(model['scale'])
    z[:,~np.asarray(model['supported'],dtype=bool)]=0.
    return model['intercept']+z@np.asarray(model['beta'])


def independent_predict(model,matrix):
    validate_model(model)
    x=np.asarray(matrix,dtype=np.float64)
    assert x.ndim==2 and x.shape[1]==model['width'] and np.isfinite(x).all()
    terms=np.zeros_like(x)
    for feature in range(model['width']):
        if model['supported'][feature]:
            terms[:,feature]=(x[:,feature]-model['mean'][feature])/model['scale'][feature]*model['beta'][feature]
    return model['intercept']+terms.sum(axis=1)
