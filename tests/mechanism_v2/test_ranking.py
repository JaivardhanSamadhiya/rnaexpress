import json
import inspect
import numpy as np
import pandas as pd
import pytest
from scipy.optimize import check_grad
from src.mechanism_v2.ranking import (RankConfig,PairedRanker,pair_design,row_weights,
    nuisance_matrix,ranking_objective)


def synthetic():
    rng=np.random.default_rng(720)
    x=rng.normal(size=(120,5))
    frame=pd.DataFrame({'dataset':np.repeat(['a','b','c'],40),
        'biological_unit':np.repeat([f'u{i}' for i in range(12)],10),
        'decision_set_id':np.repeat([f'd{i}' for i in range(12)],10),
        'candidate_id':[f'c{i}' for i in range(120)],'edit_cost':np.tile([1,3,7,20],30),
        'localization_effect':x[:,0]-0.5*x[:,1]+rng.normal(0,0.02,120)})
    return x,frame


@pytest.mark.parametrize('heads',[False,True])
def test_objective_gradient(heads):
    x,frame=synthetic();config=RankConfig(nuisance='source_size',ranking_heads=heads)
    pairs=pair_design(frame,config);diff=x[pairs['left']]-x[pairs['right']]
    matrix=nuisance_matrix(x,frame,row_weights(frame),config.nuisance)
    args=(diff,pairs['sign'],pairs['weight'],pairs['source'],matrix,config,3)
    theta=np.linspace(-0.1,0.1,5+3*heads)
    error=check_grad(lambda p:ranking_objective(p,*args)[0],lambda p:ranking_objective(p,*args)[1],theta)
    assert error<1e-6


def test_serialization_and_reproducible_predictions():
    x,frame=synthetic();names=[f'delta_{i}' for i in range(5)]
    first=PairedRanker().fit(x,frame,names)
    second=PairedRanker().fit(x,frame,names)
    restored=PairedRanker.from_record(json.loads(json.dumps(first.to_record())))
    np.testing.assert_array_equal(first.predict(x),second.predict(x))
    np.testing.assert_array_equal(first.predict(x),restored.predict(x))
    assert np.corrcoef(first.predict(x),frame.localization_effect)[0,1]>0.98


def test_latent_source_identity_separation():
    x,frame=synthetic();names=[f'delta_{i}' for i in range(5)]
    model=PairedRanker(RankConfig(ranking_heads=True)).fit(x,frame,names)
    assert list(inspect.signature(model.predict).parameters)==['features']
    before=model.predict(x)
    model.ranking_temperatures_={'a':0.1,'b':10,'c':1}
    np.testing.assert_array_equal(before,model.predict(x))
    np.testing.assert_array_equal(before,model.predict_ranking_head(x,['unseen']*len(x)))
    with pytest.raises(PermissionError):PairedRanker().fit(x,frame,['source_id','b','c','d','e'])


def test_pairs_and_weighting_are_within_units():
    _,frame=synthetic();p=pair_design(frame,RankConfig())
    assert np.array_equal(frame.decision_set_id.to_numpy()[p['left']],frame.decision_set_id.to_numpy()[p['right']])
    assert len(set(zip(p['left'],p['right'])))==len(p['left'])
    assert np.allclose(pd.Series(row_weights(frame)).groupby(frame.dataset).sum(),1/3)


def test_nuisance_matrix_is_training_only_positive_semidefinite():
    x,frame=synthetic()
    for mode in ['none','source','size','source_size']:
        m=nuisance_matrix(x,frame,row_weights(frame),mode)
        assert np.linalg.eigvalsh(m).min()>-1e-10
    with pytest.raises(ValueError):nuisance_matrix(x,frame,row_weights(frame),'illegal')
