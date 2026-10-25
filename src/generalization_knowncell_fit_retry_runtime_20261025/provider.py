"""Real deferred fixed-FIT origins bound to the fixed actually owned caller."""
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
    checkpoint_count:int
    admitted:dict
    admitted_raw:bytes


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
    return {'manifest':manifest,'request':request,'certificate':certificate,'origin':origin,'software_status':status}


def actual_owner(admitted,binding,evidence):
    """A fixed real owner verifier, never a caller-supplied Boolean/callback."""
    request=admitted['request'];generation=request['generation_manifest_sha256']
    # The owner's exact source is pinned by this runtime's source-only closure.
    common=importlib.import_module(CALLER)
    assert Path(common.__file__).resolve()==(ROOT/CALLER_SOURCE).resolve()
    common.admit_authorization(generation)
    guard.fresh_gate()
    owner=common.verify_owner('fit',generation,evidence)
    guard.fresh_gate()
    run=common.read_run(generation,evidence['run_admission_sha256'],check_commit=True)
    assert run['input_pins'][REQUEST]==binding['request_sha256']
    assert run['input_pins'][common.STATIC_BINDING]==request['static_root_binding_sha256']
    assert run['input_pins'][common.SOURCE_ADMISSION.relative_to(ROOT).as_posix()]==request['controller_source_admission_sha256']
    source=common.read_source_admission(generation,request['controller_source_admission_sha256'])
    assert source['runtime_provider_preparation_sha256']==binding['provider_preparation_manifest_sha256']
    assert common.verify_sources(generation)['files'][PREPARATION]==binding['provider_preparation_manifest_sha256']
    common.check_live_inputs(generation,evidence['run_admission_sha256'])
    return owner


def cached_source_anchors(admitted,binding,evidence):
    """Reuse initially committed evidence ONLY after fresh owned byte closure.

    No repeated per-source Git-show traversal. The real common verifier freshly
    hashes the entire generation and all admitted inputs; initially committed
    source/software evidence must be exactly included in those two closures.
    """
    common=importlib.import_module(CALLER)
    generation=admitted['request']['generation_manifest_sha256']
    manifest=common.verify_sources(generation)
    run=common.read_run(generation,evidence['run_admission_sha256'],check_commit=True)
    source=dict(admitted['manifest']['files'])
    source[PREPARATION]=binding['provider_preparation_manifest_sha256']
    source.update({SOFTWARE_STATUS:SOFTWARE_STATUS_SHA,PANDAS_ADMISSION:PANDAS_ADMISSION_SHA,
        PROFILE_ORIGIN:PROFILE_ORIGIN_SHA,PROFILE_MANIFEST:PROFILE_MANIFEST_SHA})
    for name,want in admitted['software_status']['verified_files'].items():source[PROFILE_OUT+name]=want
    for name,want in source.items():
        assert manifest['files'][name]==want,'Cached software/source evidence absent from current rehashed closure: '+name
    assert run['input_pins'][REQUEST]==binding['request_sha256']
    return True


def next_checkpoint_count(phase,key):
    if _OWNED is None:
        assert phase=='before_fit' and key is None
        return 0
    assert _OWNED.phase!='after_fit','Completed runtime provider cannot resume'
    if phase=='checkpoint':
        assert _OWNED.checkpoint_count<63 and key==CHECKPOINT_KEYS[_OWNED.checkpoint_count]
        return _OWNED.checkpoint_count+1
    assert phase=='after_fit' and key is None and _OWNED.checkpoint_count==63
    return 63


def verify_current_owned(binding,evidence,np,pd,minimize,expit):
    """Additional genuine origin check, without changing the63-phase roster."""
    global _FAILED
    assert _OWNED is not None and not _FAILED
    _FAILED=True
    assert _OWNED.binding_raw==c.canonical(binding) and _OWNED.evidence_raw==c.canonical(evidence)
    assert c.canonical(_OWNED.admitted)==_OWNED.admitted_raw
    owner=actual_owner(_OWNED.admitted,binding,evidence)
    assert cached_source_anchors(_OWNED.admitted,binding,evidence) is True
    assert original.software_objects(_OWNED.values)==(np,pd,minimize,expit)
    _,_,scipy,_,_,threadpoolctl,runtime,inventory,_=_OWNED.values
    guard.fresh_gate()
    proof=_OWNED.functions.actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    c.fresh_proof_contract(proof,_OWNED.admitted['origin'],inventory)
    guard.fresh_gate();_FAILED=False
    return owner


def provide(request_binding,owner_evidence,*,phase,task_key=None,root_start=False):
    """Before-fit, exactly63 ordered fresh checks, after-fit; no optimizer here."""
    global _OWNED,_FAILED
    assert root_start is True and not _FAILED
    _FAILED=True;guard.fresh_gate();original.source_mode()
    binding=c.binding_contract(request_binding);raw=c.canonical(binding);evidence_raw=c.canonical(owner_evidence)
    assert phase in PHASES
    count=next_checkpoint_count(phase,task_key)
    if _OWNED is None:
        assert not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in BLOCKED)
        admitted=admit(binding)
    else:
        assert _OWNED.binding_raw==raw and _OWNED.evidence_raw==evidence_raw
        assert c.canonical(_OWNED.admitted)==_OWNED.admitted_raw,'Cached admitted evidence mutated'
        admitted=admit(binding) if phase=='after_fit' else _OWNED.admitted
        assert c.canonical(admitted)==_OWNED.admitted_raw,'Initially committed source/software anchors changed'
    owner=actual_owner(admitted,binding,owner_evidence)
    assert cached_source_anchors(admitted,binding,owner_evidence) is True
    guard.fresh_gate()
    if _OWNED is None:
        functions=original.runtime_module();guard.fresh_gate();values=original.bootstrap_runtime()
    else:functions,values=_OWNED.functions,_OWNED.values
    np,pd,minimize,expit=original.software_objects(values)
    np,pd,scipy,_,_,threadpoolctl,runtime,inventory,python_proof=values
    guard.fresh_gate();initial=functions.actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    c.fresh_proof_contract(initial,admitted['origin'],inventory)
    # Ownership/source/input bytes are checked again after native-origin work.
    assert actual_owner(admitted,binding,owner_evidence)==owner
    assert cached_source_anchors(admitted,binding,owner_evidence) is True
    guard.fresh_gate();final=functions.actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    c.fresh_proof_contract(final,admitted['origin'],inventory)
    assert original.software_objects(values)==(np,pd,minimize,expit)
    original.source_mode();guard.fresh_gate()
    request=admitted['request']
    proof={'status':PROVIDER_STATUS,'stage':'fit','provider_phase':phase,
        'phase':'before_supplied_input_bridge' if phase=='before_fit' else 'before_checkpoint' if phase=='checkpoint' else 'after_campaign',
        'checkpoint_key':task_key,'checkpoint_refresh_count':count,'UTC':datetime.now(timezone.utc).isoformat(),
        'request_binding':binding,'current_pid':owner['current_pid'],'parent_pid':owner['parent_pid'],
        'caller_birth_sha256':owner['birth_sha256'],'reviewed_controller_admission_sha256':request['controller_source_admission_sha256'],
        'static_root_binding_sha256':request['static_root_binding_sha256'],
        'stable_admitted_runtime_binding_sha256':request['stable_admitted_runtime_binding_sha256'],
        'invented_only':False,'fresh_current_python_and_loaded_native_origins_checked':True,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_ADMISSION_SHA,
        'actual_origin_receipt_sha256':PROFILE_ORIGIN_SHA,'admitted_v4_profile_manifest_sha256':PROFILE_MANIFEST_SHA,
        'numpy_module_path':str(Path(np.__file__).resolve()),'numpy_module_sha256':inventory['files']['numpy/__init__.py'],
        'pandas_module_path':str(Path(pd.__file__).resolve()),'pandas_module_sha256':inventory['files']['pandas/__init__.py'],
        'numpy_version':np.__version__,'pandas_version':pd.__version__,'scipy_version':scipy.__version__,
        'initial':initial,'final':final,'python_payload_check':python_proof,'bootstrap_this_call':phase=='before_fit',
        'same_owned_software_objects_retained':True,'numerical_threads':1,'shared_source_cache_prefix':str(CACHE_PREFIX),
        'source_cache_remained_absent':True,'old_interpreter_bitwise_parity_established':False,
        'runtime_and_FIT_authority_granted_here':False,'provider_opened_project_array_or_labels':False,'optimizer_calls':0,
        'full_committed_evidence_admission_this_call':phase in ('before_fit','after_fit'),
        'fresh_source_input_bytes_owner_and_native_origins_checked':True}
    _OWNED=OwnedRuntime(raw,evidence_raw,phase,functions,values,count,admitted,c.canonical(admitted));_FAILED=False
    return {'np':np,'pd':pd,'minimize':minimize,'expit':expit,'actual_owner':owner,'fresh_origin_proof':proof,
        'fresh_origin_proof_sha256':c.digest(c.canonical(proof)),'actual_origin_receipt_sha256':PROFILE_ORIGIN_SHA}

