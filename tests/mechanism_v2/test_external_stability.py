import pickle
import numpy as np
import pytest
from src.mechanism_v2.external_stability import sequence_features,paired_features,reverse_features,StabilityPredictor


def test_external_pair_feature_arithmetic_and_orientation():
    a='ACGTAGCTACGT';b='ACGTATCTACGT'
    x=paired_features(a,b)
    np.testing.assert_allclose(x[:340],sequence_features(b)-sequence_features(a))
    np.testing.assert_array_equal(reverse_features(x[None])[0],paired_features(b,a))
    assert np.array_equal(paired_features(a,a)[:340],np.zeros(340))


@pytest.mark.parametrize('recipe',[{'id':'ridge_10','kind':'ridge','alpha':10},
    {'id':'hgb_test','kind':'hgb','max_iter':10,'max_leaf_nodes':3,'min_samples_leaf':10}])
def test_stability_model_symmetry_and_serialization(recipe):
    rng=np.random.default_rng(8);x=rng.normal(size=(90,360));y=x[:,0]-0.3*x[:,1]
    model=StabilityPredictor(recipe).fit(x,y,np.repeat(np.arange(30),3))
    restored=pickle.loads(pickle.dumps(model))  # Only our own locally generated model bytes.
    np.testing.assert_array_equal(model.predict(x),restored.predict(x))
    np.testing.assert_allclose(model.predict(reverse_features(x)),-model.predict(x),atol=0,rtol=0)
    identity=x.copy();identity[:,:340]=0
    np.testing.assert_array_equal(model.predict(identity),np.zeros(len(x)))
