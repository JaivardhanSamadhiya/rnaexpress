"""Actual guard use is deferred; no caller can inject a replacement probe."""
import hashlib
import json
import os
from pathlib import Path
import sys
from src.generalization_knowncell_joint_loader_20261022 import guard,loader
from .spec import *


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()


def digest(raw):
    assert isinstance(raw,bytes)
    return hashlib.sha256(raw).hexdigest()


def valid_hash(value):
    assert isinstance(value,str) and len(value)==64 and all(character in '0123456789abcdef' for character in value)
    return value


def decode(raw):
    assert isinstance(raw,bytes) and len(raw)<=64*2**20
    def unique(pairs):
        result={}
        for key,value in pairs:
            assert key not in result,'Duplicate supplied JSON field'
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in ()).throw(AssertionError('Nonfinite JSON token')))


def source_mode():
    assert sys.flags.no_site==1 and sys.dont_write_bytecode is True
    assert sys.pycache_prefix==str(CACHE_PREFIX) and not os.path.lexists(CACHE_PREFIX)


def fresh():
    source_mode()
    return guard.fresh_gate() # Original actual3GiB/1GiB/one-thread default probe.


def committed_bytes(name,raw,want=None):
    fresh()
    assert isinstance(name,str) and name==name.replace('\\','/') and '..' not in name.split('/')
    assert not name.startswith('/') and ':' not in name
    if want is not None:assert digest(raw)==valid_hash(want)
    loader._committed(name,raw)
    return digest(raw)


def source_bytes(name,want):
    assert name.startswith('src/') and name.endswith('.py')
    path=(ROOT/name).resolve();assert path.is_relative_to(ROOT.resolve())
    fresh();raw=guard.guarded_bytes(path,maximum=2*2**20)
    committed_bytes(name,raw,want)
    return raw


def runtime_contract(np,proof):
    """Recognize supplied actual provider proof; never manufacture acceptance."""
    assert isinstance(proof,dict) and proof['status']==PROVIDER_STATUS and proof['phase']=='after_array'
    assert proof['invented_only'] is False and proof['provider_opened_project_array'] is False
    assert proof['fresh_current_python_and_loaded_native_origins_checked'] is True
    assert proof['software_status_sha256']==SOFTWARE_STATUS_SHA and proof['software_certificate_sha256']==PANDAS_SHA
    assert proof['actual_origin_receipt_sha256']==V4_ORIGIN_SHA
    assert proof['same_owned_software_objects_retained'] is True
    assert proof['numpy_module_path']==str(NUMPY_PATH) and proof['numpy_module_sha256']==NUMPY_SHA
    assert proof['numpy_version']=='1.26.4'
    assert np.__name__=='numpy' and np.__version__=='1.26.4' and Path(np.__file__).resolve()==NUMPY_PATH.resolve()
    binding=proof['request_binding']
    assert binding['request_relative_path']=='results/generalization_knowncell_array_admission_20261023/array_request_manifest.json'
    for key in ('request_sha256','provider_preparation_manifest_sha256'):valid_hash(binding[key])
    assert binding['software_status_sha256']==SOFTWARE_STATUS_SHA and binding['pandas_admission_sha256']==PANDAS_SHA
    return digest(canonical(proof))


def bits_hash(raw,shape):
    """Exact existing engine array_hash header; supplied native float64 bytes."""
    assert sys.byteorder=='little','The fixed original Windows runtime uses little endian float64'
    assert len(raw)==8*__import__('math').prod(shape)
    return digest(canonical({'shape':list(shape),'dtype':'float64','order':'C'})+raw)
