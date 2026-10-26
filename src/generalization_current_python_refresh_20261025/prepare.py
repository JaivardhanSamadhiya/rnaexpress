"""Preparation source/old-metadata closure only; never inventory live software."""
import ast
import datetime
import json
from pathlib import Path
import sys
import time
import unittest
from . import spec
from .contracts import decode, digest, relative_key


def raw_sha(path):
    return digest(Path(path).read_bytes())


def save(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')


def run():
    assert sys.dont_write_bytecode and sys.flags.no_site
    assert sys.pycache_prefix and Path(sys.pycache_prefix).resolve()==spec.SOURCE_CACHE.resolve()
    assert not spec.SOURCE_CACHE.exists()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino') for name in sys.modules)
    for name,want in spec.PRIOR_PINS.items():
        assert raw_sha(spec.ROOT/name)==want,name
    from . import tests
    started=time.monotonic()
    suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    sources={p.relative_to(spec.ROOT).as_posix():raw_sha(p) for p in sorted(spec.SRC.glob('*.py'))}
    for name in sources:ast.parse((spec.ROOT/name).read_text(encoding='utf-8'),filename=name)
    receipt={'status':'PASS_INVENTED_STDLIB_REFRESH_CONTRACT_TESTS_NO_LIVE_INVENTORY',
        'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'elapsed_seconds':time.monotonic()-started,
        'source_sha256':sources,'live_software_inventory_executed':False,'native_origin_probe_executed':False,
        'absent_source_cache_prefix':str(spec.SOURCE_CACHE),
        'scientific_packages_imported':False,'biological_inputs_read':False,'model_fits':0}
    receipt_path=spec.OUT/'synthetic_tests_receipt.json';save(receipt_path,receipt)
    files=dict(spec.PRIOR_PINS)
    # Prior V4 is immutable source/provenance closure, not renewed compatibility.
    old=decode((spec.ROOT/spec.V4_MANIFEST).read_bytes())
    for name,want in old['files'].items():
        relative_key(name)
        assert name not in files or files[name]==want
        assert raw_sha(spec.ROOT/name)==want,name
        files[name]=want
    paths=list(spec.SRC.iterdir())+list(spec.REP.iterdir())+[receipt_path,spec.OUT/'.gitattributes',spec.ROOT/'src/__init__.py']
    for path in paths:
        if path.is_file():files[path.relative_to(spec.ROOT).as_posix()]=raw_sha(path)
    imported={}
    for name,module in tuple(sys.modules.items()):
        source=getattr(module,'__file__',None)
        if not source:continue
        path=Path(source).resolve()
        if path.is_relative_to(spec.ROOT) and path.suffix=='.py':
            key=path.relative_to(spec.ROOT).as_posix()
            assert files.get(key)==raw_sha(path),'Unpinned imported workspace module: '+key
            imported[name]=key
    manifest={'status':spec.PREPARATION_STATUS,'namespace':spec.NS,
        'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':dict(sorted(files.items())),
        'file_count':len(files),'imported_workspace_source_closure':imported,
        'synthetic_tests_receipt_sha256':raw_sha(receipt_path),
        'inventory_execution_authorized_here':False,'numerical_compatibility_established':False,
        'old_certificates_or_sources_changed':False,'native_origin_probe_executed':False,
        'future_root_command_module':'src.'+spec.NS+'.inventory',
        'future_command_requires_initial_preparation_SHA_and_exact_HEAD_bytes':True}
    save(spec.MANIFEST,manifest)
    print('SOURCE_PREPARATION_ONLY',len(files),raw_sha(spec.MANIFEST),flush=True)


if __name__=='__main__':run()
