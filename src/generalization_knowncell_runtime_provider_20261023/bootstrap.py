"""Additive import ordering, preserving original V3 software/payload checks.

Actual original resource checks surround each top-level scientific import.
No guard replacement and no patch of any original module are performed.
"""
import importlib
import json
from src.generalization_knowncell_joint_loader_20261022 import guard
from src.generalization_knowncell_parser_profile_v3_20261023 import common as v3


def load_scientific():
    modules = []
    for name in ('numpy','pandas','scipy','scipy.optimize','scipy.special','threadpoolctl'):
        guard.fresh_gate()
        modules.append(importlib.import_module(name))
        guard.fresh_gate()
    np,pd,scipy,optimize,special,threadpoolctl = modules
    return np,pd,scipy,optimize.minimize,special.expit,threadpoolctl


def bootstrap():
    guard.fresh_gate()
    from src.generalization_knowncell_parser_profile_20261022 import runtime as base_runtime
    from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
    # These are the same V3 envelope and two-cache checks; only the sequence of
    # resource checks/top-level imports is additive. No case, data or fit runs.
    inventory = json.loads(guard.guarded_bytes(v3.INVENTORY,maximum=32*2**20))
    base = json.loads(guard.guarded_bytes(v3.BASE_INVENTORY,maximum=32*2**20))
    old = json.loads(guard.guarded_bytes(v3.RUNTIME,maximum=32*2**20))
    assert inventory['base_inventory_sha256']==v3.sha(v3.BASE_INVENTORY)
    assert inventory['old_runtime_receipt_sha256']==v3.sha(v3.RUNTIME)
    assert inventory['additional_cache_files']==v3.ADDITIONAL_CACHES
    assert inventory['files']==v3.expanded_files(base['files'],old['files'])
    assert inventory['native_files']==base['native_files']
    for name,want in v3.ADDITIONAL_CACHES.items():
        path = v3.PREFIX/name
        assert not path.is_symlink() and path.resolve().is_relative_to(v3.PREFIX.resolve())
        assert v3.sha(path)==want,'Explicit V3 root cache changed before import'
    launcher.clean_import_state()
    guard.fresh_gate()
    runtime,original_inventory,python_proof = base_runtime.current_payload()
    assert original_inventory==base
    guard.fresh_gate()
    base_runtime.select_closed_scientific_path()
    values = load_scientific()
    return (*values,runtime,inventory,python_proof)
