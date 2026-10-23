"""Source controls only, preserving original metadata admission and floors."""
import hashlib
import json
import os
from pathlib import Path
import sys
from src.generalization_knowncell_metadata_execution_20261023 import common as original

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_knowncell_metadata_execution_v2_20261023'
OUT=ROOT/'results'/NS
MANIFEST=OUT/'execution_manifest.json'
CACHE_PREFIX=OUT/'source_cache_must_remain_absent'
V1_MANIFEST='results/generalization_knowncell_metadata_execution_20261023/execution_manifest.json'
V1_SHA='242b5905fdeaa72c77bb65389830c88d868da215b717f2b7c459d0a99cc8d7c9'
SRC_INIT='src/__init__.py'
SRC_INIT_SHA='f2119a6b4b46bae5262a99c4bba45dea895dd587b86d3edd0a7703ea6dbade19'
BUNDLE=original.BUNDLE
ADMISSION=original.ADMISSION
THREAD_KEYS=original.THREAD_KEYS
STATUS='FROZEN_ORIGINAL_FLOOR_SOURCE_CACHE_BYPASS_METADATA_V2'
resource_failure=original.resource_failure
sha=original.sha
canonical=original.canonical
save_new=original.save_new


def source_mode():
    assert sys.flags.no_site==1,'Require -S before importing project modules'
    assert sys.dont_write_bytecode is True,'Require -B'
    assert sys.pycache_prefix==str(CACHE_PREFIX),'Require exact -X pycache_prefix argument'
    assert not os.path.lexists(CACHE_PREFIX),'Source cache prefix must remain absent; never create it'
    return {'no_site':True,'dont_write_bytecode':True,'pycache_prefix':str(CACHE_PREFIX),
            'cache_prefix_absent':True,'normal_source_cache_reads_bypassed':True}


def valid_sha(value):
    assert isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    return value


def read_json(raw):
    def unique(pairs):
        result={}
        for key,value in pairs:
            assert key not in result,'Duplicate JSON key'
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=unique)


def verify_sources(expected_sha):
    source_mode();valid_sha(expected_sha)
    raw=MANIFEST.read_bytes()
    assert sha(raw)==expected_sha,'Execution manifest differs from initially committed bytes'
    manifest=read_json(raw);assert manifest['status']==STATUS
    assert manifest['source_cache_prefix']==str(CACHE_PREFIX)
    assert manifest['files'][V1_MANIFEST]==V1_SHA and manifest['files'][SRC_INIT]==SRC_INIT_SHA
    for name,want in manifest['files'].items():
        assert name==name.replace('\\','/') and not name.startswith('/') and ':' not in name and '..' not in name.split('/')
        assert sha((ROOT/name).read_bytes())==want,name
    source_mode()
    return manifest


def interpreter(manifest):
    assert Path(sys.executable).resolve()==Path(manifest['python_executable']).resolve()
    assert sys.version_info[:2]==(3,12) and sys.implementation.cache_tag=='cpython-312'
    expected={Path(sys.executable).resolve(),Path(sys.executable).resolve().parent/'python3.dll',
              Path(sys.executable).resolve().parent/'python312.dll'}
    assert {Path(name).resolve() for name in manifest['python_native_files']}==expected
    for name,want in manifest['python_native_files'].items():assert sha(Path(name).read_bytes())==want,name
    return True
