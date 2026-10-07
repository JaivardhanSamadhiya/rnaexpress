"""Identical convex solver with a source-only fixed penalty grid."""
from types import SimpleNamespace
from .common import TRACKS
from src.generalization_20261007.route_scaling import fit_model,predict_model

CONFIGS=[{'id':'pair_005','penalty':.005,'scaling':'pair'},
         {'id':'pair_05','penalty':.05,'scaling':'pair'},
         {'id':'pair_5','penalty':.5,'scaling':'pair'}]


def module(track):
    assert track in TRACKS
    return SimpleNamespace(CONFIGS=CONFIGS,fit_model=fit_model,predict_model=predict_model)
