"""Fresh relocated software inventory, with real C: Git/source provenance."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
BASE=Path('C:/Users/jaisa/rnaexpress-recovery-20261025/material_snapshot_20261025')
NS='generalization_cdrive_software_inventory_20261025'
OUT=ROOT/'results'/NS
READY=OUT/'source_readiness.json'
PREFIX=ROOT/'data/interim/mechanism_v2/runtime'
CACHE=ROOT/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
GIT=Path('C:/Program Files/Git/mingw64/bin/git.exe')
COPY_SHA='a10f4a3fd85c6e24887ed0d8756d7d351c21ce4e51057ac0fc7cb56876e4d4f5'
DISCOVERY='results/generalization_current_python_refresh_v2_20261025/current_native_discovery.json'
DISCOVERY_SHA='1b7f635bc7fc0abb8cf02321f63b24c2ec95e4dce4dd11ec645e565ecf2b4782'
BASE_INVENTORY='results/generalization_knowncell_parser_profile_20261022/payload_inventory.json'
EXPANDED='results/generalization_knowncell_parser_profile_v3_20261023/payload_inventory.json'
OLD_FIT='results/generalization_knowncell_fit_paged_execution_20261025/preparation_manifest.json'
OLD_FIT_SHA='4a8d83023675d17cdc4af37801dc69df4b2c49d7b397a2cfd6ba1aa8b519d632'
STATUS='PASS_CDRIVE_CURRENT42_UNCHANGED7998_BYTES_COMPATIBILITY_PENDING'


def raw_sha(raw):return hashlib.sha256(raw).hexdigest()


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):value.update(block)
    return value.hexdigest()


def save(path,value):
    with path.open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def mode():
    assert ROOT.resolve()==(BASE/'workspace').resolve()
    assert sys.flags.no_site==1 and sys.dont_write_bytecode
    assert sys.pycache_prefix==str(CACHE) and not CACHE.exists()
    assert os.environ.get('PYTHONUTF8')=='1'
    assert sys.implementation.cache_tag=='cpython-312' and sys.version_info[:3]==(3,12,14)
    assert not any(n.split('.')[0] in ('numpy','pandas','scipy','torch','openvino') for n in sys.modules)


def read_bound(path,want):
    assert not path.is_symlink()
    raw=path.read_bytes();assert raw_sha(raw)==want,str(path)
    return json.loads(raw)


def prepare():
    mode()
    old=read_bound(ROOT/OLD_FIT,OLD_FIT_SHA)
    read_bound(BASE/'copy_independently_verified.json',COPY_SHA)
    pins={OLD_FIT:OLD_FIT_SHA,DISCOVERY:DISCOVERY_SHA}
    for name in (BASE_INVENTORY,EXPANDED):pins[name]=old['files'][name]
    for name,want in pins.items():read_bound(ROOT/name,want)
    for kind in ('src','reports','results','artifacts'):
        folder=ROOT/kind/NS
        for path in folder.iterdir():
            if path.is_file():pins[path.relative_to(ROOT).as_posix()]=sha(path)
    save(READY,{'status':'FROZEN_CDRIVE_RELOCATED_SOFTWARE_BYTE_INVENTORY_NOT_NUMERICAL_ADMISSION',
        'files':pins,'private_material_verification_sha256':COPY_SHA,
        'actual_selected_scientific_prefix':str(PREFIX),'native_discovery_sha256':DISCOVERY_SHA,
        'scientific_or_stage_authority_granted':False})
    print('CDRIVE_SOURCE_READY',sha(READY),flush=True)


def sources(expected):
    mode();raw=READY.read_bytes();assert raw_sha(raw)==expected
    value=json.loads(raw)
    assert value['status']=='FROZEN_CDRIVE_RELOCATED_SOFTWARE_BYTE_INVENTORY_NOT_NUMERICAL_ADMISSION'
    for name,want in value['files'].items():assert sha(ROOT/name)==want,name
    read_bound(BASE/'copy_independently_verified.json',COPY_SHA)
    return value


def run(expected):
    started=time.monotonic();sources(expected)
    assert sha(GIT)=='51c6331aab2426ae2df187975590587b5a10042e3423f4bc0fdcb54aeb3efab7'
    assert subprocess.check_output([str(GIT),'show','HEAD:'+READY.relative_to(ROOT).as_posix()],cwd=ROOT,creationflags=8)==READY.read_bytes()
    save(OUT/'inventory_attempt_birth.json',{'status':'ONE_CDRIVE_RELOCATED_BYTE_INVENTORY_STARTED',
        'UTC':datetime.now(timezone.utc).isoformat(),'preparation_manifest_sha256':expected,'pid':os.getpid()})
    current=None
    try:
        ready=sources(expected)
        base=read_bound(ROOT/BASE_INVENTORY,ready['files'][BASE_INVENTORY])
        expanded=read_bound(ROOT/EXPANDED,ready['files'][EXPANDED])
        discovery=read_bound(ROOT/DISCOVERY,DISCOVERY_SHA)
        native=discovery['current_native_files'];assert len(native)==42
        assert str(Path(sys.executable).resolve())==discovery['python_executable'] and sys.version==discovery['python_version']
        files=expanded['files'];assert len(files)==7998
        actual=set()
        for component in base['components']:
            path=PREFIX/component
            assert path.exists() and not path.is_symlink()
            for item in ([path] if path.is_file() else path.rglob('*')):
                assert not item.is_symlink()
                if item.is_file():actual.add(item.relative_to(PREFIX).as_posix())
        actual.update(expanded['additional_cache_files'])
        assert actual==set(files)
        for name,want in {**{str(PREFIX/key):value for key,value in files.items()},**native}.items():
            current=name;assert time.monotonic()-started<=300
            assert shutil.disk_usage(BASE).free>=2*2**30
            path=Path(name);before=path.stat();assert not path.is_symlink()
            assert sha(path)==want,name
            after=path.stat();assert (before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns)
        sources(expected)
        for name,want in native.items():assert sha(name)==want,name
        assert shutil.disk_usage(BASE).free>=2*2**30 and time.monotonic()-started<=300
        result={'status':STATUS,'UTC':datetime.now(timezone.utc).isoformat(),
            'initial_preparation_manifest_sha256':expected,'native_discovery_sha256':DISCOVERY_SHA,
            'historical_V4_acceptance_reused_for_new_Python':False,
            'python_executable':str(Path(sys.executable).resolve()),'python_version':sys.version,
            'python_cache_tag':sys.implementation.cache_tag,'current_bundled_stdlib_native_files':native,
            'current_native_file_count':42,'changed_native_file_count':38,
            'selected_scientific_payload_files':files,'selected_scientific_payload_file_count':7998,
            'actual_selected_scientific_prefix':str(PREFIX),'historical_source_prefix':base['prefix'],
            'private_material_verification_sha256':COPY_SHA,'storage_relocation_explicitly_verified':True,
            'unchanged_versions_from_package_metadata':base['versions'],
            'two_explicit_possible_cache_payloads':expanded['additional_cache_files'],
            'actually_loaded_python_DLL_origins_verified':False,'scientific_packages_imported':False,
            'numerical_compatibility_established':False,'biological_inputs_read':False,'biological_model_fits':0,
            'stage_authority_granted':False,'old_exact_runtime_identity_passes':False,
            'source_cache_prefix':str(CACHE),'source_cache_prefix_exists':False,
            'deadline_semantics':'cooperative300-second checks between I/O operations',
            'elapsed_seconds':time.monotonic()-started}
        save(OUT/'current_python_inventory_cdrive.json',result)
        print(STATUS,sha(OUT/'current_python_inventory_cdrive.json'),flush=True)
    except BaseException as error:
        save(OUT/'inventory_failure.json',{'status':'FAILED_CDRIVE_BYTE_INVENTORY_PRESERVED_NO_RETRY',
            'exception_type':type(error).__name__,'error':str(error),'current_source':current,
            'scientific_or_runtime_admission_granted':False})
        raise


if __name__=='__main__':
    if sys.argv[1:]==['--prepare']:prepare()
    else:
        assert len(sys.argv)==3 and sys.argv[1]=='--expected-preparation-sha'
        run(sys.argv[2])
