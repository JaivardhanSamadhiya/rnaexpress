"""Real deferred provider with one bootstrap and request-bound origin refresh.

No provider function runs at import. All resources are checked through the
original default real guard. There is no caller-supplied guard or bootstrap.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import importlib
import os
from pathlib import Path
import sys

from .spec import *
from . import contracts as c
from src.generalization_knowncell_joint_loader_20261022 import guard, loader


@dataclass
class OwnedRuntime:
    binding_raw:bytes
    phase:str
    functions:object
    values:tuple


_OWNED = None
_FAILED = False


def source_mode():
    assert sys.flags.no_site==1 and sys.flags.dont_write_bytecode==1,'Worker must start with -S -B'
    assert sys.dont_write_bytecode is True
    assert sys.implementation.cache_tag=='cpython-312' and sys.version_info[:2]==(3,12)
    assert sys.pycache_prefix==str(CACHE_PREFIX) and not os.path.lexists(CACHE_PREFIX),'Exact shared absent cache prefix required'
    assert all(os.environ.get(key)=='1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'))
    assert os.environ.get('PYTHONUTF8')=='1' and os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'


def read_bound(name,expected,*,committed=True):
    path = c.relative(name)
    raw = guard.guarded_bytes(path,maximum=32*2**20)
    assert c.digest(raw)==c.hash_contract(expected),name
    if committed:
        loader._committed(name,raw)  # Original real fresh gate and pinned direct Git, no callback override.
    return raw


def admit(binding):
    """Only fixed software/source objects and the caller-owned committed request."""
    raw = read_bound(PREPARATION,binding['provider_preparation_manifest_sha256'])
    manifest = c.decode(raw)
    assert manifest['status']==PREPARATION_STATUS
    assert manifest['runtime_provider_module']==MODULE and manifest['runtime_provider_qualname']=='provide'
    assert manifest['data_access_authorized'] is False and manifest['actual_runtime_provider_invoked'] is False
    assert manifest['shared_cache_prefix']==str(CACHE_PREFIX)
    for name,sha in manifest['files'].items():
        assert static_allowed(name),'Unexpected nonsoftware payload in source closure'
        read_bound(name,sha)
    request_raw = read_bound(binding['request_relative_path'],binding['request_sha256'])
    request = c.decode(request_raw)
    c.request_contract(request,binding,manifest['files'][SOURCE])
    status = c.decode(read_bound(SOFTWARE_STATUS,SOFTWARE_STATUS_SHA))
    certificate = c.decode(read_bound(PANDAS_ADMISSION,PANDAS_ADMISSION_SHA))
    origin = c.decode(read_bound(PROFILE_ORIGIN,PROFILE_ORIGIN_SHA))
    profile = c.decode(read_bound(PROFILE_MANIFEST,PROFILE_MANIFEST_SHA))
    c.software_contract(status,certificate,origin,profile)
    for name,sha in status['verified_files'].items():
        assert name in ('preparation_manifest.json','actual_origin_receipt.json','invented_profile_receipt.json',
                        'pandas_admission_candidate.json','supervisor_receipt.json')
        read_bound(PROFILE_OUT+name,sha)
    assert Path(sys.executable).resolve()==Path(certificate['python_executable']).resolve()
    assert sys.implementation.cache_tag==certificate['python_cache_tag']=='cpython-312'
    executable = Path(sys.executable).resolve()
    natives = {Path(name).resolve():sha for name,sha in certificate['python_native_files'].items()}
    assert len(natives)==3 and set(natives)=={executable,executable.parent/'python3.dll',executable.parent/'python312.dll'}
    for path,sha in natives.items():
        assert c.digest(guard.guarded_bytes(path,maximum=32*2**20))==sha
    return {'manifest':manifest,'origin':origin,'certificate':certificate}


def runtime_module():
    # This source-only module is imported only after the real resource and byte
    # admission checks. Its bootstrap contains the original scientific imports.
    return importlib.import_module(RUNTIME_MODULE)


def bootstrap_runtime():
    from .bootstrap import bootstrap
    return bootstrap()


def software_objects(values):
    np,pd,scipy,minimize,expit,threadpoolctl,runtime,inventory,python_proof = values
    for module,name,version in ((np,'numpy','1.26.4'),(pd,'pandas','2.2.3'),(scipy,'scipy','1.14.1')):
        assert sys.modules.get(name) is module and module.__name__==name and module.__version__==version
        assert Path(module.__file__).resolve()==SCIENTIFIC_PREFIX.resolve()/name/'__init__.py'
    assert sys.modules.get('threadpoolctl') is threadpoolctl
    assert minimize is sys.modules['scipy.optimize'].minimize and expit is sys.modules['scipy.special'].expit
    assert callable(minimize) and callable(expit)
    return np,pd,minimize,expit


def provide(request_binding,*,phase,root_start=False):
    """Real runtime-only API; first before_array, then after_array exactly once.

    No request is created here. Both calls require the SAME already committed
    array request and evidence. No other stage is accepted automatically.
    Failure poisons this process; the root must preserve it rather than retry.
    """
    global _OWNED,_FAILED
    assert root_start is True,'Explicit caller root-start required for the actual authorized stage'
    assert not _FAILED,'A failed provider cannot resume in this process'
    _FAILED = True
    guard.fresh_gate()  # No resource callback parameter: use the original real probe.
    source_mode()
    binding = c.binding_contract(request_binding)
    bound_raw = c.canonical(binding)
    assert phase in PHASES
    if _OWNED is None:
        assert phase=='before_array','Initial phase must bootstrap before_array'
        assert not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in BLOCKED),'Fresh process required'
    else:
        assert _OWNED.binding_raw==bound_raw,'Runtime request or software binding changed'
        assert _OWNED.phase=='before_array' and phase=='after_array','Unsupported duplicate or post phase'
    admission = admit(binding)
    guard.fresh_gate()
    if _OWNED is None:
        functions = runtime_module()
        guard.fresh_gate()
        values = bootstrap_runtime()
    else:
        functions,values = _OWNED.functions,_OWNED.values
    np,pd,minimize,expit = software_objects(values)
    np,pd,scipy,_,_,threadpoolctl,runtime,inventory,python_proof = values
    guard.fresh_gate()
    initial = functions.actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    c.fresh_proof_contract(initial,admission['origin'],inventory)
    guard.fresh_gate()
    final_admission = admit(binding)
    assert c.canonical(final_admission)==c.canonical(admission),'Source or software evidence changed during import/proof'
    guard.fresh_gate()
    final = functions.actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    c.fresh_proof_contract(final,admission['origin'],inventory)
    software_objects(values)
    source_mode()
    guard.fresh_gate()
    proof = {'status':PROVIDER_STATUS,'UTC':datetime.now(timezone.utc).isoformat(),
             'request_binding':binding,'phase':phase,'invented_only':False,
             'provider_opened_project_array':False,'provider_opened_labels_or_fit_inputs':False,
             'fresh_current_python_and_loaded_native_origins_checked':True,
             'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_ADMISSION_SHA,
             'actual_origin_receipt_sha256':PROFILE_ORIGIN_SHA,
             'admitted_v4_profile_manifest_sha256':PROFILE_MANIFEST_SHA,
             'numpy_module_path':str(Path(np.__file__).resolve()),'numpy_module_sha256':inventory['files']['numpy/__init__.py'],
             'numpy_version':np.__version__,'pandas_version':pd.__version__,
             'initial':initial,'final':final,'python_payload_check':python_proof,
             'bootstrap_this_call':phase=='before_array','same_owned_software_objects_retained':True,
             'shared_source_cache_prefix':str(CACHE_PREFIX),'source_cache_remained_absent':True,
             'old_interpreter_bitwise_parity_established':False,
             'input_or_FIT_admission_granted_here':False,'model_fits':0}
    proof_sha = c.digest(c.canonical(proof))
    _OWNED = OwnedRuntime(bound_raw,phase,functions,values)
    _FAILED = False
    return {'np':np,'pd':pd,'minimize':minimize,'expit':expit,
            'actual_origin_receipt_sha256':PROFILE_ORIGIN_SHA,
            'fresh_origin_proof':proof,'fresh_origin_proof_sha256':proof_sha}
