"""Exactly nine original source pools; no optimizer/campaign or FIT authority."""
import os
from . import common as c
from src.generalization_knowncell_joint_loader_20261022 import guard
from src.generalization_knowncell_joint_engine_20261023 import adapter_v2 as adapter
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lifecycle
from src.generalization_knowncell_joint_input_bridge_20261023 import sampler as original_sampler


def prepare_original_pools(np,pd,bridge_result,array_certificate):
    guard.fresh_gate()
    stable_proof=array_certificate['runtime_acceptance_after_array']
    sampler=original_sampler.load_original_sampler(np,stable_proof,root_start=True)
    assert isinstance(sampler,original_sampler.GuardedSampler)
    prepared=adapter.prepare_pools(np,pd,sampler,bridge_result['metadata'],bridge_result['features'],bridge_result['effects'],
        probe=guard.live_resources,environment=os.environ,admissions=bridge_result['admissions'])
    assert isinstance(prepared,adapter.PreparedPools) and len(prepared.pools)==9
    lifecycle.validate_prefit(prepared.prefit_document)
    for key,pool in prepared.pools.items():
        guard.fresh_gate()
        assert adapter.original.pool_binding(np,pool)==pool['binding']==prepared.prefit_document['source_pools'][key]
    return prepared,sampler.identity

