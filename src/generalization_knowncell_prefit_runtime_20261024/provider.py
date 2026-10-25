"""Real deferred prefit origins bound to the fixed actually owned caller."""
from dataclasses import dataclass
from datetime import datetime,timezone
import importlib
from pathlib import Path
import sys
from src.generalization_knowncell_runtime_provider_20261023 import provider as original
from src.generalization_knowncell_joint_loader_20261022 import guard
from . import contracts as c
from .spec import *


@dataclass
class OwnedRuntime:
    binding_raw:bytes
    evidence_raw:bytes
    phase:str
    functions:object
    values:tuple


_OWNED=None
_FAILED=False


def admit(binding):
    manifest=c.decode(original.read_bound(PREPARATION,binding['provider_preparation_manifest_sha256']))
    assert manifest['status']==PREPARATION_STATUS and manifest['runtime_provider_module']==MODULE
    assert manifest['actual_runtime_invoked'] is False and manifest['data_access_authorized'] is False
    assert manifest['shared_cache_prefix']==str(CACHE_PREFIX)
    for name,want in manifest['files'].items():
        assert static_allowed(name),'Unexpected source/software object'
        original.read_bound(name,want)
    request=c.decode(original.read_bound(REQUEST,binding['request_sha256']))
    c.request_contract(request,binding,manifest['files'][SOURCE])
    status=c.decode(original.read_bound(SOFTWARE_STATUS,SOFTWARE_STATUS_SHA))
    certificate=c.decode(original.read_bound(PANDAS_ADMISSION,PANDAS_ADMISSION_SHA))
    origin=c.decode(original.read_bound(PROFILE_ORIGIN,PROFILE_ORIGIN_SHA))
    profile=c.decode(original.read_bound(PROFILE_MANIFEST,PROFILE_MANIFEST_SHA))
    c.software_contract(status,certificate,origin,profile)
    for name,want in status['verified_files'].items():
        assert name in ('preparation_manifest.json','actual_origin_receipt.json','invented_profile_receipt.json',
                        'pandas_admission_candidate.json','supervisor_receipt.json')
        original.read_bound(PROFILE_OUT+name,want)
    assert Path(sys.executable).resolve()==Path(certificate['python_executable']).resolve()
    assert sys.implementation.cache_tag==certificate['python_cache_tag']=='cpython-312'
    executable=Path(sys.executable).resolve()
    natives={Path(name).resolve():want for name,want in certificate['python_native_files'].items()}
    assert len(natives)==len(certificate['python_native_files'])==3
    assert set(natives)=={executable,executable.parent/'python3.dll',executable.parent/'python312.dll'}
    for path,want in natives.items():assert c.digest(guard.guarded_bytes(path,maximum=32*2**20))==want
    return {'manifest':manifest,'request':request,'certificate':certificate,'origin':origin}


def actual_owner(admitted,binding,evidence):
    """A fixed real owner verifier, never a caller-supplied Boolean/callback."""
    request=admitted['request'];generation=request['generation_manifest_sha256']
    # The owner's exact source is pinned by this runtime's source-only closure.
    common=importlib.import_module(CALLER)
    assert Path(common.__file__).resolve()==(ROOT/CALLER_SOURCE).resolve()
    common.admit_authorization(generation)
    guard.fresh_gate()
    owner=common.verify_owner('prefit',generation,evidence)
    guard.fresh_gate()
    run=common.read_run(generation,evidence['run_admission_sha256'],check_commit=True)
    assert run['input_pins'][REQUEST]==binding['request_sha256']
    assert run['input_pins'][common.STATIC_BINDING]==request['static_root_binding_sha256']
    assert run['input_pins'][common.SOURCE_ADMISSION.relative_to(ROOT).as_posix()]==request['controller_source_admission_sha256']
    source=common.read_source_admission(generation,request['controller_source_admission_sha256'])
    assert source['runtime_provider_preparation_sha256']==binding['provider_preparation_manifest_sha256']
    assert common.verify_sources(generation)['files'][PREPARATION]==binding['provider_preparation_manifest_sha256']
    return owner


def provide(request_binding,owner_evidence,*,phase,root_start=False):
    """Exactly before/after prefit in the same actual owned worker; no optimizer."""
    global _OWNED,_FAILED
    assert root_start is True and not _FAILED
    _FAILED=True;guard.fresh_gate();original.source_mode()
    binding=c.binding_contract(request_binding);raw=c.canonical(binding);evidence_raw=c.canonical(owner_evidence)
    assert phase in PHASES
    if _OWNED is None:
        assert phase=='before_prefit'
        assert not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in BLOCKED)
    else:
        assert _OWNED.binding_raw==raw and _OWNED.evidence_raw==evidence_raw
        assert _OWNED.phase=='before_prefit' and phase=='after_prefit'
    admitted=admit(binding);owner=actual_owner(admitted,binding,owner_evidence);guard.fresh_gate()
    if _OWNED is None:
        functions=original.runtime_module();guard.fresh_gate();values=original.bootstrap_runtime()
    else:functions,values=_OWNED.functions,_OWNED.values
    original.software_objects(values)
    np,pd,scipy,_,_,threadpoolctl,runtime,inventory,python_proof=values
    guard.fresh_gate();initial=functions.actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    c.fresh_proof_contract(initial,admitted['origin'],inventory)
    guard.fresh_gate();final_admission=admit(binding)
    assert c.canonical(final_admission)==c.canonical(admitted)
    assert actual_owner(final_admission,binding,owner_evidence)==owner
    guard.fresh_gate();final=functions.actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    c.fresh_proof_contract(final,admitted['origin'],inventory)
    original.software_objects(values);original.source_mode();guard.fresh_gate()
    request=admitted['request']
    proof={'status':PROVIDER_STATUS,'stage':'prefit','provider_phase':phase,
        'phase':'before_supplied_input_bridge' if phase=='before_prefit' else 'after_pool_preparation',
        'UTC':datetime.now(timezone.utc).isoformat(),'request_binding':binding,
        'current_pid':owner['current_pid'],'parent_pid':owner['parent_pid'],'caller_birth_sha256':owner['birth_sha256'],
        'reviewed_controller_admission_sha256':request['controller_source_admission_sha256'],
        'static_root_binding_sha256':request['static_root_binding_sha256'],
        'stable_admitted_runtime_binding_sha256':request['stable_admitted_runtime_binding_sha256'],
        'invented_only':False,'fresh_current_python_and_loaded_native_origins_checked':True,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_ADMISSION_SHA,
        'actual_origin_receipt_sha256':PROFILE_ORIGIN_SHA,'admitted_v4_profile_manifest_sha256':PROFILE_MANIFEST_SHA,
        'numpy_module_path':str(Path(np.__file__).resolve()),'numpy_module_sha256':inventory['files']['numpy/__init__.py'],
        'pandas_module_path':str(Path(pd.__file__).resolve()),'pandas_module_sha256':inventory['files']['pandas/__init__.py'],
        'numpy_version':np.__version__,'pandas_version':pd.__version__,'scipy_version':scipy.__version__,
        'initial':initial,'final':final,'python_payload_check':python_proof,
        'bootstrap_this_call':phase=='before_prefit','same_owned_software_objects_retained':True,
        'numerical_threads':1,'shared_source_cache_prefix':str(CACHE_PREFIX),'source_cache_remained_absent':True,
        'old_interpreter_bitwise_parity_established':False,'runtime_and_FIT_authority_granted_here':False,
        'provider_opened_project_array_or_labels':False,'optimizer_calls':0}
    _OWNED=OwnedRuntime(raw,evidence_raw,phase,functions,values);_FAILED=False
    return {'np':np,'pd':pd,'actual_owner':owner,'fresh_origin_proof':proof,
            'fresh_origin_proof_sha256':c.digest(c.canonical(proof)),
            'actual_origin_receipt_sha256':PROFILE_ORIGIN_SHA}
