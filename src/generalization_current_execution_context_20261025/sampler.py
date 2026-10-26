"""New epoch factory reusing only exact extractor/GuardedSampler algorithms."""
import ast
import hashlib
import itertools
from . import contracts as c,current,spec
from src.generalization_knowncell_joint_input_bridge_20261023 import sampler as original


def _compile_supplied(np,model_raw,common_raw,current_proof_sha256):
    """Private supplied-source primitive; no present runtime authority is implied."""
    assert c.digest(model_raw)==original.MODEL_SHA and c.digest(common_raw)==original.COMMON_SHA
    c.sha(current_proof_sha256)
    node,identity=original.extract_function(model_raw,common_raw)
    module=ast.Module(body=[node],type_ignores=[]);before=ast.dump(node,include_attributes=False)
    code=compile(module,str(spec.ROOT/original.MODEL_SOURCE),'exec')
    scope={'__name__':original.ORIGINAL_MODULE,'np':np,'hashlib':hashlib,'itertools':itertools,
        'PAIR_CACHE':{},'SEED':original.SEED}
    exec(code,scope)
    assert ast.dump(module.body[0],include_attributes=False)==before
    assert set(scope)=={'__name__','np','hashlib','itertools','PAIR_CACHE','SEED','__builtins__','pair_indices'}
    identity.update({'new_factory_kind':'CURRENT_EPOCH_EXACT_EXTRACTOR_AND_GUARDED_WRAPPER',
        'old_sampler_runtime_contract_called':False,'supplied_proof_independently_verified_here':False})
    return original.GuardedSampler(scope['pair_indices'],np,identity,current_proof_sha256)


def load_current_sampler(*args,**kwargs):
    current.require_real_owned_fit_context(*args,**kwargs)
    raise AssertionError('Unreachable until fixed real current owner/provider integration is implemented')
