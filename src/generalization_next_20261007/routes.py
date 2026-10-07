"""One fixed solver shared by every feature comparison."""
from types import SimpleNamespace
from src.generalization_20261007.route_scaling import fit_model, predict_model
from .common import TRACKS

def module(track):
    assert track in TRACKS
    configs = [{'id':track+'_l2_'+name, 'penalty':penalty, 'scaling':'pair'}
               for name, penalty in [('005', .005), ('05', .05), ('5', .5)]]
    return SimpleNamespace(CONFIGS=configs, fit_model=fit_model, predict_model=predict_model)
