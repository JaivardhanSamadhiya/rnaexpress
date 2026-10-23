"""Source/static declarations only. Never follows any array/metadata-data alias."""
import ast
from datetime import datetime,timezone
import sys
from . import admit as a
from .spec import *


def run():
    # No actual request, provider acceptance, metadata bundle or array is opened.
    contract_raw=(ROOT/ARRAY_CONTRACT).read_bytes();assert a.sha(contract_raw)==ARRAY_CONTRACT_SHA
    contract=a.loader.json_bytes(contract_raw)
    assert contract['status']=='SOURCE_ONLY_SUPPLIED_ARRAY_CONTRACT_NOT_PROJECT_ADMISSION'
    pins=a.normalize_map(contract['files'])
    for name,want in pins.items():
        assert a.static_pin_allowed(name),name
        assert a.sha((ROOT/name).read_bytes())==want,name
    prefit_raw=(ROOT/SOURCE_PREFIT).read_bytes();assert a.sha(prefit_raw)==SOURCE_PREFIT_SHA
    prefit=a.loader.json_bytes(prefit_raw);assert prefit['status']=='FROZEN_PREFIT'
    source=a.normalize_map(prefit['files'])
    for name,want in DECLARED_PINS.items():assert source[name]==want
    status_raw=(ROOT/SOFTWARE_STATUS).read_bytes();assert a.sha(status_raw)==SOFTWARE_STATUS_SHA
    cert_raw=(ROOT/SOFTWARE_CERT).read_bytes();assert a.sha(cert_raw)==SOFTWARE_CERT_SHA
    a.software_contract(a.loader.json_bytes(status_raw),a.loader.json_bytes(cert_raw))
    for name,raw in ((ARRAY_CONTRACT,contract_raw),(SOURCE_PREFIT,prefit_raw),(SOFTWARE_STATUS,status_raw),(SOFTWARE_CERT,cert_raw)):
        pins[name]=a.sha(raw)
    test_path=OUT/'synthetic_tests_receipt.json';test=a.loader.json_bytes(test_path.read_bytes())
    assert test['status']=='PASS_INVENTED_STDLIB_GUARDED_ARRAY_API_TESTS'
    assert test['actual_native_resource_probes']==test['actual_NumPy_calls']==test['project_array_reads']==test['project_metadata_reads']==test['project_outcome_reads']==test['models_fitted']==0
    assert test['scientific_runtimes_imported'] is False and test['project_admission_granted'] is False
    own=sorted(SRC.glob('*.py'))
    assert test['source_files']=={path.relative_to(ROOT).as_posix():a.sha(path.read_bytes()) for path in own}
    # Imported workspace modules are stdlib-only source dependencies, not payloads.
    for module in tuple(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            path=Path(name).resolve()
            if path.is_relative_to((ROOT/'src').resolve()):
                assert path.suffix=='.py';own.append(path)
    own+= [SRC/'.gitattributes',REP/'.gitattributes',OUT/'.gitattributes',REP/'protocol.md',test_path]
    for path in sorted(set(own)):
        name=path.relative_to(ROOT).as_posix();assert a.static_pin_allowed(name),name
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw.decode('utf-8'),filename=name)
        pins[name]=a.sha(raw)
    assert not any(name.split('.')[0] in {'numpy','pandas','scipy','torch','openvino'} for name in sys.modules)
    payload={'status':'SOURCE_ONLY_GUARDED_ARRAY_API_NOT_PROJECT_ADMISSION',
        'generated_utc':datetime.now(timezone.utc).isoformat(),'files':pins,
        'declared_future_payload_pins_NOT_opened':DECLARED_PINS,'source_prefit_sha256':SOURCE_PREFIT_SHA,
        'expected_row_ids_sha256':ROW_IDS_SHA,'metadata_bundle_path_NOT_opened':METADATA_BUNDLE,
        'required_future_array_request':REQUEST,'shared_absent_cache_prefix':str(CACHE_PREFIX),
        'public_future_certificate_status':STATUS,'software_profile_is_not_biological_admission':True,
        'provider_preparation_and_actual_runtime_acceptance_REQUIRED':True,
        'future_request_requires_runtime_import_authorized_true':True,
        'fresh_resource_RAM_floor':3*2**30,'fresh_resource_disk_floor':2**30,'numerical_threads':1,
        'PUM_resource_exception_applies':False,'PRELib_resource_exception_applies':False,
        'compressed_NPZ_cap':MAX_NPZ,'project_array_reads':0,'project_metadata_reads':0,'project_outcome_reads':0,
        'models_fitted':0,'scientific_runtimes_imported':False,'actual_native_resource_probes':0,
        'array_request_created':False,'actual_provider_called':False,'label_or_FIT_admission_granted':False,
        'certificate_writer_implemented':False,'root_exclusive_save_and_commit_still_required':True}
    target=ROOT/READY
    with target.open('xb') as handle:handle.write(a.canonical(payload))
    print('SOURCE_ONLY_GUARDED_ARRAY_API_READY',len(pins),a.sha(target.read_bytes()),flush=True)


if __name__=='__main__':run()
