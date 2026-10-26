"""Deferred root-started current42/old7998 byte check; no numerical authority."""
import datetime
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from src.generalization_current_python_refresh_20261025.contracts import (
    compare_inventory,decode,digest,payload_contract,relative_key,valid_sha,
)
from src.generalization_current_python_refresh_20261025.inventory import (
    enumerate_native,enumerate_payload,prior_documents,safe_file,save,sha,stable_file_hash,
)
from . import spec
from .contracts import bind_discovery
from .discover import preconditions


def initial_manifest(expected):
    assert valid_sha(expected)
    raw=spec.MANIFEST.read_bytes()
    assert digest(raw)==expected,'Explicit root preparation SHA mismatch'
    committed=subprocess.check_output(['git','show','HEAD:'+spec.MANIFEST.relative_to(spec.ROOT).as_posix()],
        cwd=spec.ROOT,creationflags=0x8 if os.name=='nt' else 0)
    assert committed==raw,'Preparation not exactly committed to HEAD'
    document=decode(raw)
    assert document['status']==spec.PREPARATION_STATUS
    for name,want in document['files'].items():
        relative_key(name)
        assert sha(safe_file(spec.ROOT/name,spec.ROOT))==want,name
    key=spec.DISCOVERY.relative_to(spec.ROOT).as_posix()
    assert document['files'][key]==document['native_discovery_sha256']
    return document,raw


def run(expected):
    started=time.monotonic();preconditions()
    manifest,initial=initial_manifest(expected)
    save(spec.OUT/'inventory_attempt_birth.json',{
        'status':'STARTED_CURRENT42_OLD7998_BYTE_INVENTORY_NOT_NATIVE_OR_NUMERICAL_PROBE',
        'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),
        'initial_preparation_manifest_sha256':digest(initial)})
    try:
        prior=prior_documents()
        base,expanded,old=(prior[name] for name in (spec.BASE_PAYLOAD,spec.PAYLOAD,spec.OLD_RUNTIME))
        payload=payload_contract(base,expanded,old,spec.ADDITIONAL_CACHES,base['components'])
        discovery_raw=spec.DISCOVERY.read_bytes()
        assert digest(discovery_raw)==manifest['native_discovery_sha256']
        discovery=decode(discovery_raw)
        expected_native,changes=bind_discovery(discovery,base['current_python_native_files'],
            spec.NEW_NATIVE_BY_BASENAME,str(spec.EXPECTED_PYTHON.parent),spec.DISCOVERY_STATUS)
        old_python=prior[spec.PRIOR_PYTHON]
        assert old_python['python_version']==base['python_version']==discovery['python_version']==sys.version
        assert Path(old_python['python_executable']).resolve()==spec.EXPECTED_PYTHON.resolve()
        assert old_python['python_native_files'].items()<=base['current_python_native_files'].items()
        assert Path(base['prefix']).resolve()==Path(old['runtime_path']).resolve()==spec.PREFIX.resolve()
        selected=enumerate_payload(spec.PREFIX,base['components'],spec.ADDITIONAL_CACHES)
        observed={name:stable_file_hash(path)[0] for name,path in selected.items()}
        compare_inventory(payload,observed,'Selected unchanged scientific payload')
        native_paths=enumerate_native(spec.EXPECTED_PYTHON.parent)
        records={name:stable_file_hash(path) for name,path in native_paths.items()}
        native={name:item[0] for name,item in records.items()}
        compare_inventory(expected_native,native,'Fixed current42 native discovery')
        assert spec.MANIFEST.read_bytes()==initial,'Preparation changed during inventory'
        for name,want in manifest['files'].items():assert sha(spec.ROOT/name)==want,name
        preconditions()
        result={'status':spec.INVENTORY_STATUS,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'initial_preparation_manifest_sha256':digest(initial),'native_discovery_sha256':digest(discovery_raw),
            'prior_pins':spec.PRIOR_PINS,'historical_V4_acceptance_reused_for_new_Python':False,
            'python_executable':str(Path(sys.executable).resolve()),'python_version':sys.version,
            'python_cache_tag':sys.implementation.cache_tag,'current_bundled_stdlib_native_files':native,
            'current_native_file_metadata':{name:item[1] for name,item in records.items()},
            'current_native_file_count':42,'changed_native_file_count':38,
            'changes_from_22October_native_inventory':changes,
            'selected_scientific_payload_files':observed,'selected_scientific_payload_file_count':7998,
            'unchanged_versions_from_package_metadata':base['versions'],
            'two_explicit_possible_cache_payloads':spec.ADDITIONAL_CACHES,'cache_execution_claimed':False,
            'source_cache_prefix':str(spec.SOURCE_CACHE),'source_cache_prefix_exists':False,
            'actually_loaded_python_DLL_origins_verified':False,'all_stdlib_source_bytes_inventoried':False,
            'scientific_packages_imported':False,'numerical_compatibility_established':False,
            'old_interpreter_bitwise_parity_established':False,'old_exact_runtime_identity_passes':False,
            'cause_or_exact_time_of_binary_change_established':False,'biological_inputs_read':False,
            'biological_model_fits':0,'stage_authority_granted':False,
            'old_sources_certificates_prefix_and_guards_changed':False,
            'inventory_elapsed_seconds':time.monotonic()-started}
        save(spec.OUT/'current_python_inventory_refresh.json',result)
        print('CURRENT42_OLD7998_INVENTORY_ONLY_COMPATIBILITY_PENDING',sha(spec.OUT/'current_python_inventory_refresh.json'),flush=True)
        return result
    except BaseException as error:
        save(spec.OUT/'inventory_failure.json',{'status':'FAILED_REFRESH_V2_ATTEMPT_PRESERVED_NO_RETRY',
            'initial_preparation_manifest_sha256':digest(initial),'exception_type':type(error).__name__,
            'error':str(error),'traceback':traceback.format_exc(),'elapsed_seconds':time.monotonic()-started,
            'scientific_packages_imported':False,'biological_inputs_read':False,'compatibility_established':False})
        raise


if __name__=='__main__':
    assert len(sys.argv)==3 and sys.argv[1]=='--expected-preparation-sha'
    run(sys.argv[2])
