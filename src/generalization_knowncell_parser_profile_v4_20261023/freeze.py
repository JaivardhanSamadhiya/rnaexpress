"""Freeze a separate bound attempt without changing the unexecuted V3 input."""
import ast
import json
import sys
from .common import *


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    assert sha(BASE_MANIFEST)==BASE_MANIFEST_SHA
    base=json.loads(BASE_MANIFEST.read_bytes())
    assert len(base['files'])==99
    for name,want in base['files'].items():assert sha(ROOT/name)==want,name
    test_path=OUT/'stdlib_test_receipt.json';test=json.loads(test_path.read_bytes())
    assert test['status']=='PASS_INVENTED_INITIAL_MANIFEST_BINDING_ONLY' and test['tests_run']==12
    sources=sorted(SRC.glob('*.py'))
    assert test['source_sha256']=={path.relative_to(ROOT).as_posix():sha(path) for path in sources}
    for path in sources:ast.parse(path.read_text(encoding='utf-8'))
    files=dict(base['files'])
    additions=[BASE_MANIFEST,*sources,*REP.glob('*'),SRC/'.gitattributes',OUT/'.gitattributes',
               test_path,OUT/'stdlib_tests_attempt_01.log']
    files.update({path.relative_to(ROOT).as_posix():sha(path) for path in additions if path.is_file()})
    result={key:value for key,value in base.items() if key!='files'}
    result.update(status=STATUS,files=files,separate_attempt_namespace=NS,
        preserved_unexecuted_v3_manifest_sha256=sha(BASE_MANIFEST),
        initially_git_verified_raw_sha_retained=True,child_expected_manifest_sha_required=True,
        unchanged_manifest_required_before_bootstrap_output_and_completion=True,
        scientific_case_expansion=False,native_execution=False,
        same_science_runtime_cache_admissions_caps_threads_and_deadline_as_v3=True)
    jsave(MANIFEST,result)
    print('BOUND_V4_PREPARATION_FROZEN',len(files),sha(MANIFEST),flush=True)


if __name__=='__main__':run()
