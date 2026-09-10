import numpy as np
from src.mechanism_v2.stability_validation import group_mse,group_mean,select_recipe


def test_external_metrics_balance_groups_not_rows():
    y=np.array([1.,1.,1.,3.]);groups=np.array(['a','a','a','b'])
    assert group_mean(y,groups)==2.
    assert group_mse(y,np.zeros(4),groups)==5.


def test_external_inner_selection_is_deterministic():
    rng=np.random.default_rng(12);x=rng.normal(size=(48,360));groups=np.repeat(np.arange(8),6)
    y=x[:,0];recipes=[{'id':'ridge_10','kind':'ridge','alpha':10},{'id':'ridge_100','kind':'ridge','alpha':100}]
    first=select_recipe(x,y,groups,recipes);second=select_recipe(x,y,groups,recipes)
    assert first==second
    assert first[0]['id'] in {'ridge_10','ridge_100'}
