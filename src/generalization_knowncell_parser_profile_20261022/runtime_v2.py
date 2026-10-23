"""Additive existing-cache check after the unchanged v1 native/source proof."""
import sys
from .runtime import bootstrap, actual_proof as original_proof
from .cache_integrity_v2 import possible_cache_proof
from .common import PREFIX


def actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory):
    result=original_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    result['possible_bytecode_payload_proof']=possible_cache_proof(sys.modules,PREFIX,inventory['files'])
    return result
