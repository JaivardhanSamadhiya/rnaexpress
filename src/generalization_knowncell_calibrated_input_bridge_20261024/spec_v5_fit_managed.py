"""Separate immutable static binding for one explicitly authorized fresh FIT."""
from .spec_v3 import *
READY='results/'+NS+'/preparation_manifest_v5_fit_managed_20261025.json'


def binding_path(stage):
    assert stage=='fit','This additive binding path is only for the one proposed fresh FIT'
    return 'results/'+NS+'/root_bindings_v5_fit_managed_20261025.json'
