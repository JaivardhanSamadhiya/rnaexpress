"""Explicitly authorized raw42-file discovery; no scientific package scanning."""
import datetime
import os
from pathlib import Path
import sys
import time
from src.generalization_current_python_refresh_20261025.contracts import decode,digest
from src.generalization_current_python_refresh_20261025.inventory import (
    enumerate_native,save,sha,stable_file_hash,
)
from . import spec
from .contracts import full_native_contract


def preconditions():
    assert Path(sys.executable).resolve() == spec.EXPECTED_PYTHON.resolve()
    assert sys.version_info[:3] == (3,12,14) and sys.implementation.cache_tag == 'cpython-312'
    assert sys.flags.no_site and sys.dont_write_bytecode and os.environ.get('PYTHONUTF8') == '1'
    assert sys.pycache_prefix and Path(sys.pycache_prefix).resolve() == spec.SOURCE_CACHE.resolve()
    assert not spec.SOURCE_CACHE.exists()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino') for name in sys.modules)


def run():
    preconditions();started=time.monotonic()
    raw=(spec.ROOT/spec.PAYLOAD).read_bytes()
    assert digest(raw) == spec.PRIOR_PINS[spec.PAYLOAD]
    prior=decode(raw)
    assert prior['python_version'] == sys.version
    paths=enumerate_native(spec.EXPECTED_PYTHON.parent)
    records={name:stable_file_hash(path) for name,path in paths.items()}
    current={name:item[0] for name,item in records.items()}
    changes=full_native_contract(prior['current_python_native_files'],current,
        spec.NEW_NATIVE_BY_BASENAME,str(spec.EXPECTED_PYTHON.parent))
    metadata={name:dict(item[1],mtime_UTC=datetime.datetime.fromtimestamp(
        item[1]['mtime_ns']/1e9,datetime.timezone.utc).isoformat(),
        ctime_UTC=datetime.datetime.fromtimestamp(item[1]['ctime_ns']/1e9,datetime.timezone.utc).isoformat())
        for name,item in records.items()}
    preconditions()
    value={'status':spec.DISCOVERY_STATUS,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'python_executable':str(Path(sys.executable).resolve()),'python_version':sys.version,
        'python_cache_tag':sys.implementation.cache_tag,'prior_payload_inventory_sha256':digest(raw),
        'current_native_files':current,'native_file_metadata':metadata,'native_file_count':42,
        'changed_file_count':38,'unchanged_file_count':4,'changes_from_prior_inventory':changes,
        'root_reported_three_anchor_hashes':spec.NEW_NATIVE_BY_BASENAME,
        'actually_loaded_DLL_origins_verified':False,'numerical_compatibility_established':False,
        'scientific_packages_imported':False,'scientific_payload_files_read':0,
        'biological_inputs_read':False,'model_fits':0,'stage_authority_granted':False,
        'cause_or_exact_time_of_binary_change_established':False,
        'elapsed_seconds':time.monotonic()-started,'discovery_source_sha256':sha(__file__)}
    save(spec.DISCOVERY,value)
    print('RAW_NATIVE_DISCOVERY_ONLY',42,len(changes),sha(spec.DISCOVERY),flush=True)
    return value


if __name__=='__main__':
    assert sys.argv[1:] == ['--discover-current-native-bytes-only']
    run()
