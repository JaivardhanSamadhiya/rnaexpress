"""Bind source/metadata/current42 discovery, without scanning scientific bytes."""
import ast
import datetime
import json
from pathlib import Path
import sys
import time
import unittest
from src.generalization_current_python_refresh_20261025.contracts import decode,digest
from src.generalization_current_python_refresh_20261025.inventory import save,sha
from . import spec
from .contracts import bind_discovery
from .discover import preconditions


def run():
    preconditions()
    assert sha(spec.V1_MANIFEST)==spec.V1_MANIFEST_SHA
    v1=decode(spec.V1_MANIFEST.read_bytes())
    files={spec.V1_MANIFEST.relative_to(spec.ROOT).as_posix():spec.V1_MANIFEST_SHA}
    for name,want in v1['files'].items():
        assert sha(spec.ROOT/name)==want,name
        files[name]=want
    raw=(spec.ROOT/spec.PAYLOAD).read_bytes()
    assert digest(raw)==spec.PRIOR_PINS[spec.PAYLOAD]
    base=decode(raw)
    discovery=decode(spec.DISCOVERY.read_bytes())
    bind_discovery(discovery,base['current_python_native_files'],spec.NEW_NATIVE_BY_BASENAME,
        str(spec.EXPECTED_PYTHON.parent),spec.DISCOVERY_STATUS)
    assert discovery['discovery_source_sha256']==sha(spec.SRC/'discover.py')
    from . import tests
    started=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    assert result.wasSuccessful()
    own={p.relative_to(spec.ROOT).as_posix():sha(p) for p in sorted(spec.SRC.glob('*.py'))}
    for name in own:ast.parse((spec.ROOT/name).read_text(encoding='utf-8'),filename=name)
    receipt={'status':'PASS_INVENTED_CURRENT42_REFRESH_V2_SOURCE_TESTS_NO_SCIENTIFIC_INVENTORY',
        'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'elapsed_seconds':time.monotonic()-started,
        'source_sha256':own,'native_discovery_sha256':sha(spec.DISCOVERY),
        'actual7998_scientific_inventory_executed':False,'native_origin_probe_executed':False,
        'scientific_packages_imported':False,'biological_inputs_read':False,'model_fits':0}
    receipt_path=spec.OUT/'synthetic_tests_receipt.json';save(receipt_path,receipt)
    paths=list(spec.SRC.iterdir())+list(spec.REP.iterdir())+[
        spec.OUT/'.gitattributes',spec.DISCOVERY,receipt_path,spec.UNUSED_NOTE]
    for path in paths:
        if path.is_file():files[path.relative_to(spec.ROOT).as_posix()]=sha(path)
    imported={}
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if not path:continue
        path=Path(path).resolve()
        if path.is_relative_to(spec.ROOT) and path.suffix=='.py':
            key=path.relative_to(spec.ROOT).as_posix()
            assert files.get(key)==sha(path),'Unpinned imported workspace source: '+key
            imported[name]=key
    manifest={'status':spec.PREPARATION_STATUS,'namespace':spec.NS,
        'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':dict(sorted(files.items())),
        'file_count':len(files),'native_discovery_sha256':sha(spec.DISCOVERY),
        'synthetic_tests_receipt_sha256':sha(receipt_path),'imported_workspace_source_closure':imported,
        'native_file_count':42,'known_changed_native_file_count':38,
        'actual7998_scientific_inventory_executed':False,'numerical_compatibility_established':False,
        'future_root_module':'src.'+spec.NS+'.inventory',
        'future_inventory_requires_exact_initial_manifest_SHA_and_HEAD_bytes':True,
        'stage_authority_granted':False}
    save(spec.MANIFEST,manifest)
    print('V2_SOURCE_PREPARATION_ONLY',len(files),sha(spec.MANIFEST),flush=True)


if __name__=='__main__':run()
