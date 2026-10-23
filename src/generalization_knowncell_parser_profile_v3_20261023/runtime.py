"""Original scientific bootstrap; exact two-cache expansion before execution."""
import json
import sys
from src.generalization_knowncell_parser_profile_20261022.runtime import (
    bootstrap as original_bootstrap,actual_proof as original_proof,
)
from .common import *
from .cache_integrity import possible_cache_proof


def bootstrap():
    inventory=json.loads(INVENTORY.read_bytes());base=json.loads(BASE_INVENTORY.read_bytes())
    old=json.loads(RUNTIME.read_bytes())
    assert inventory['base_inventory_sha256']==sha(BASE_INVENTORY)
    assert inventory['old_runtime_receipt_sha256']==sha(RUNTIME)
    assert inventory['additional_cache_files']==ADDITIONAL_CACHES
    assert inventory['files']==expanded_files(base['files'],old['files'])
    assert inventory['native_files']==base['native_files']
    for name,want in ADDITIONAL_CACHES.items():
        path=PREFIX/name
        assert not path.is_symlink() and path.resolve().is_relative_to(PREFIX.resolve())
        assert sha(path)==want,'Explicit root cache changed before import: '+str(path)
    values=original_bootstrap()
    np,pd,scipy,minimize,expit,threadpoolctl,runtime,original_inventory,python_proof=values
    assert original_inventory==base
    return np,pd,scipy,minimize,expit,threadpoolctl,runtime,inventory,python_proof


def actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory):
    result=original_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    result['possible_bytecode_payload_proof']=possible_cache_proof(sys.modules,PREFIX,inventory['files'])
    result['two_explicit_root_cache_admissions']=ADDITIONAL_CACHES
    result['v3_payload_inventory_sha256']=sha(INVENTORY)
    result['failed_v2_preparation_preserved_sha256']=sha(BASE_MANIFEST)
    return result
