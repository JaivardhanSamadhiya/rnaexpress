"""Request-bound labels runtime, using unchanged reviewed bootstrap/proofs."""
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import sys
from src.generalization_knowncell_runtime_provider_20261023 import provider as original
from src.generalization_knowncell_joint_loader_20261022 import guard
from . import contracts as c
from .spec import *


@dataclass
class OwnedRuntime:
    binding_raw:bytes
    phase:str
    functions:object
    values:tuple


_OWNED=None
_FAILED=False


def admit(binding):
    manifest=c.decode(original.read_bound(PREPARATION,binding['provider_preparation_manifest_sha256']))
    assert manifest['status']==PREPARATION_STATUS
    assert manifest['runtime_provider_module']==MODULE and manifest['runtime_provider_qualname']=='provide'
    assert manifest['actual_runtime_invoked'] is False and manifest['data_access_authorized'] is False
    assert manifest['shared_cache_prefix']==str(CACHE_PREFIX)
    for name,want in manifest['files'].items():
        assert static_allowed(name),'Unexpected payload in software preparation'
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
    native={Path(name).resolve():want for name,want in certificate['python_native_files'].items()}
    assert len(native)==len(certificate['python_native_files'])==3
    assert set(native)=={executable,executable.parent/'python3.dll',executable.parent/'python312.dll'}
    for path,want in native.items():assert c.digest(guard.guarded_bytes(path,maximum=32*2**20))==want
    return {'manifest':manifest,'certificate':certificate,'origin':origin}


def provide(request_binding,*,phase,root_start=False):
    """Exactly before_labels then after_labels; no reads, execution or fit here."""
    global _OWNED,_FAILED
    assert root_start is True and not _FAILED
    _FAILED=True
    guard.fresh_gate();original.source_mode()
    binding=c.binding_contract(request_binding);binding_raw=c.canonical(binding)
    assert phase in PHASES
    if _OWNED is None:
        assert phase=='before_labels'
        assert not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in BLOCKED)
    else:
        assert _OWNED.binding_raw==binding_raw and _OWNED.phase=='before_labels' and phase=='after_labels'
    admitted=admit(binding)
    guard.fresh_gate()
    if _OWNED is None:
        functions=original.runtime_module();guard.fresh_gate()
        # Original reviewed helper gates each top-level scientific import.
        values=original.bootstrap_runtime()
    else:functions,values=_OWNED.functions,_OWNED.values
    original.software_objects(values)
    np,pd,scipy,minimize,expit,threadpoolctl,runtime,inventory,python_proof=values
    guard.fresh_gate()
    initial=functions.actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    c.fresh_proof_contract(initial,admitted['origin'],inventory)
    guard.fresh_gate();final_admission=admit(binding)
    assert c.canonical(final_admission)==c.canonical(admitted)
    guard.fresh_gate()
    final=functions.actual_proof(np,pd,scipy,threadpoolctl,runtime,inventory)
    c.fresh_proof_contract(final,admitted['origin'],inventory)
    original.software_objects(values);original.source_mode();guard.fresh_gate()
    proof={'status':PROVIDER_STATUS,'UTC':datetime.now(timezone.utc).isoformat(),
        'request_binding':binding,'phase':phase,'invented_only':False,
        'provider_opened_project_array':False,'provider_opened_labels_or_fit_inputs':False,
        'fresh_current_python_and_loaded_native_origins_checked':True,
        'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_ADMISSION_SHA,
        'actual_origin_receipt_sha256':PROFILE_ORIGIN_SHA,'admitted_v4_profile_manifest_sha256':PROFILE_MANIFEST_SHA,
        'numpy_module_path':str(Path(np.__file__).resolve()),'numpy_module_sha256':inventory['files']['numpy/__init__.py'],
        'pandas_module_path':str(Path(pd.__file__).resolve()),'pandas_module_sha256':inventory['files']['pandas/__init__.py'],
        'numpy_version':np.__version__,'pandas_version':pd.__version__,
        'initial':initial,'final':final,'python_payload_check':python_proof,
        'bootstrap_this_call':phase=='before_labels','same_owned_software_objects_retained':True,
        'shared_source_cache_prefix':str(CACHE_PREFIX),'source_cache_remained_absent':True,
        'old_interpreter_bitwise_parity_established':False,'input_or_FIT_admission_granted_here':False,'model_fits':0}
    _OWNED=OwnedRuntime(binding_raw,phase,functions,values);_FAILED=False
    return {'np':np,'pd':pd,'minimize':minimize,'expit':expit,'actual_origin_receipt_sha256':PROFILE_ORIGIN_SHA,
            'fresh_origin_proof':proof,'fresh_origin_proof_sha256':c.digest(c.canonical(proof))}
