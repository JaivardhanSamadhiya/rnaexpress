"""Extract the exact old sampler AST; never import its modeling module."""
import ast
import hashlib
import itertools
from .spec import *
from . import contracts as c


def extract_function(model_bytes,common_bytes):
    """Pure source inspection used by preparation and invented-only tests."""
    model=ast.parse(model_bytes.decode('utf-8'),filename=MODEL_SOURCE)
    common=ast.parse(common_bytes.decode('utf-8'),filename=COMMON_SOURCE)
    functions=[node for node in model.body if isinstance(node,ast.FunctionDef) and node.name=='pair_indices']
    assert len(functions)==1
    node=functions[0]
    assert not node.decorator_list and node.returns is None
    assert len(node.args.args)==1 and node.args.args[0].arg=='frame'
    assert not node.args.posonlyargs and not node.args.kwonlyargs and not node.args.defaults
    assert node.args.vararg is None and node.args.kwarg is None
    seeds=[node.value.value for node in common.body if isinstance(node,ast.Assign)
        and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='SEED'
        and isinstance(node.value,ast.Constant)]
    assert seeds==[SEED],'Original sole seed declaration changed'
    caches=[node for node in model.body if isinstance(node,ast.Assign) and len(node.targets)==1
        and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='PAIR_CACHE']
    assert len(caches)==1 and isinstance(caches[0].value,ast.Dict) and not caches[0].value.keys
    segment=ast.get_source_segment(model_bytes.decode('utf-8'),node)
    identity={'original_model_source_sha256':c.digest(model_bytes),'original_common_source_sha256':c.digest(common_bytes),
        'original_function_source_sha256':c.digest(segment.encode()),
        'original_function_AST_sha256':c.digest(ast.dump(node,include_attributes=False).encode()),
        'original_seed':SEED,'original_seed_source':COMMON_SOURCE,
        'compiled_only_original_function':True,'broad_model_module_imported':False,
        'wrapper_is_new_bridge_code_not_original_function':True}
    return node,identity


class GuardedSampler:
    """Transparent wrapper identity expected by the deferred existing engine."""
    __name__='pair_indices'
    __module__=ORIGINAL_MODULE
    def __init__(self,function,np,identity,runtime_sha):
        self._original=function;self._np=np;self._cache=function.__globals__['PAIR_CACHE']
        self.identity=dict(identity);self.identity['supplied_actual_runtime_proof_sha256']=runtime_sha
        self._failed=False
    def __call__(self,frame):
        assert not self._failed,'A failed sampler handle cannot resume'
        self._failed=True
        c.fresh() # Even a cache hit must pass the actual original resource gate.
        scope=self._original.__globals__
        assert scope['np'] is self._np and scope['hashlib'] is hashlib and scope['itertools'] is itertools
        assert scope['PAIR_CACHE'] is self._cache and scope['SEED']==SEED and scope['__name__']==ORIGINAL_MODULE
        result=self._original(frame) # No changed AST, RNG, pair roster or old weights.
        c.fresh()
        self._failed=False
        return result


def load_original_sampler(np,actual_runtime_proof,*,root_start=False):
    """Factory only; future controller separately binds this bridge's sources."""
    assert root_start is True
    c.fresh();runtime_sha=c.runtime_contract(np,actual_runtime_proof)
    model=c.source_bytes(MODEL_SOURCE,MODEL_SHA);common=c.source_bytes(COMMON_SOURCE,COMMON_SHA)
    node,identity=extract_function(model,common)
    assert identity['original_model_source_sha256']==MODEL_SHA and identity['original_common_source_sha256']==COMMON_SHA
    module=ast.Module(body=[node],type_ignores=[])
    before=ast.dump(node,include_attributes=False)
    c.fresh()
    code=compile(module,str(ROOT/MODEL_SOURCE),'exec')
    scope={'__name__':ORIGINAL_MODULE,'np':np,'hashlib':hashlib,'itertools':itertools,'PAIR_CACHE':{},'SEED':SEED}
    c.fresh();exec(code,scope) # Defines exactly one function; no old import/top-level execution.
    assert ast.dump(module.body[0],include_attributes=False)==before
    function=scope['pair_indices']
    assert function.__name__=='pair_indices' and function.__module__==ORIGINAL_MODULE
    assert set(scope)=={'__name__','np','hashlib','itertools','PAIR_CACHE','SEED','__builtins__','pair_indices'}
    own='src/'+NS+'/sampler.py'
    c.fresh();wrapper=c.guard.guarded_bytes(ROOT/own,maximum=2*2**20)
    c.committed_bytes(own,wrapper)
    identity.update({'guard_wrapper_source':own,'guard_wrapper_source_sha256':c.digest(wrapper),
                     'original_compiled_code_filename':function.__code__.co_filename,
                     'original_algorithm_native_parity_certified_here':False})
    c.fresh()
    return GuardedSampler(function,np,identity,runtime_sha)
